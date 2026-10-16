import os
from pathlib import Path
from time import perf_counter
from sqlalchemy import create_engine, event
from performance import record
from sqlalchemy import inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + Path(__file__).with_name("Nerochi.db").as_posix())

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 10} if DATABASE_URL.startswith("sqlite:") else {})


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _record):
    if DATABASE_URL.startswith("sqlite:"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA busy_timeout = 10000")
        cursor.execute("PRAGMA synchronous = FULL")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def start_sql_timer(connection, cursor, statement, parameters, context, executemany):
    context._neurochi_sql_start = perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def finish_sql_timer(connection, cursor, statement, parameters, context, executemany):
    record("sql", (perf_counter() - context._neurochi_sql_start) * 1000)
    record("sql_queries", 1)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema_compatibility():
    """Apply small SQLite migrations while preserving existing user data."""
    inspector = inspect(engine)
    if DATABASE_URL.startswith("sqlite:"):
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA journal_mode = WAL")
    with engine.begin() as connection:
        if "games" in inspector.get_table_names():
            game_columns = {column["name"] for column in inspector.get_columns("games")}
            if "source_game_id" not in game_columns:
                connection.execute(text("ALTER TABLE games ADD COLUMN source_game_id INTEGER"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_games_source_game_id ON games (source_game_id)"))
        if "game_responses" in inspector.get_table_names():
            game_columns = {column["name"] for column in inspector.get_columns("game_responses")}
            if "test_session_id" not in game_columns:
                connection.execute(text("ALTER TABLE game_responses ADD COLUMN test_session_id INTEGER REFERENCES child_test_sessions(id)"))
        session_columns = {
            column["name"] for column in inspector.get_columns("child_test_sessions")
        } if "child_test_sessions" in inspector.get_table_names() else set()

        if "completed_at" not in session_columns:
            connection.execute(text("ALTER TABLE child_test_sessions ADD COLUMN completed_at DATETIME"))
        if "updated_at" not in session_columns:
            connection.execute(text("ALTER TABLE child_test_sessions ADD COLUMN updated_at DATETIME"))

        if "test_answers" in inspector.get_table_names():
            answer_columns = {
                column["name"] for column in inspector.get_columns("test_answers")
            }
            if "chosen_option_text" not in answer_columns:
                connection.execute(text("ALTER TABLE test_answers ADD COLUMN chosen_option_text VARCHAR"))

            # Keep the latest answer before adding the uniqueness guarantee.
            connection.execute(text("""
                DELETE FROM test_answers
                WHERE id NOT IN (
                    SELECT MAX(id) FROM test_answers GROUP BY session_id, question_id
                )
            """))
            connection.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_test_answers_session_question
                ON test_answers (session_id, question_id)
            """))

            # Backfill the human-readable option without changing the scoring code.
            connection.execute(text("""
                UPDATE test_answers
                SET chosen_option_text = CASE chosen_option
                    WHEN 'A' THEN (SELECT option_A FROM questions WHERE questions.id = test_answers.question_id)
                    WHEN 'B' THEN (SELECT option_B FROM questions WHERE questions.id = test_answers.question_id)
                    WHEN 'C' THEN (SELECT option_C FROM questions WHERE questions.id = test_answers.question_id)
                    ELSE chosen_option
                END
                WHERE chosen_option_text IS NULL OR chosen_option_text = ''
            """))

        if "chat_messages" in inspector.get_table_names():
            message_columns = {
                column["name"] for column in inspector.get_columns("chat_messages")
            }
            if "session_id" not in message_columns:
                connection.execute(text("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER"))
            if "sources_json" not in message_columns:
                connection.execute(text("ALTER TABLE chat_messages ADD COLUMN sources_json TEXT"))

        # create_all does not add indexes to existing tables.
        indexes = {
            "children": ("user_id",),
            "chat_messages": ("session_id, timestamp, id", "user_id, child_id"),
            "chat_sessions": ("user_id, child_id, updated_at, id",),
            "child_test_sessions": ("child_id, is_completed, completed_at", "question_set_id"),
            "game_responses": ("child_id, timestamp", "test_session_id"),
            "growth_records": ("child_id, date, id",),
            "questions": ("question_set_id, order_index",),
        }
        for table, column_sets in indexes.items():
            if table not in inspector.get_table_names():
                continue
            for columns in column_sets:
                name = "ix_perf_" + table + "_" + columns.replace(", ", "_")
                connection.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})"))

    # SQLite cannot alter a NOT NULL column in place.  Rebuild only the
    # session table when upgrading installations that predate general chat;
    # IDs are copied unchanged, so ChatMessage.session_id remains valid.
    inspector = inspect(engine)
    if "chat_sessions" not in inspector.get_table_names():
        return
    session_columns = {
        column["name"]: column for column in inspector.get_columns("chat_sessions")
    }
    child_column = session_columns.get("child_id")
    if child_column is None or child_column.get("nullable", False):
        return

    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
        connection.commit()
        try:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            connection.exec_driver_sql("""
                CREATE TABLE chat_sessions__general_chat_migration (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    child_id INTEGER,
                    title VARCHAR NOT NULL,
                    summary_text TEXT,
                    summary_until_message_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(child_id) REFERENCES children(id)
                )
            """)
            connection.exec_driver_sql("""
                INSERT INTO chat_sessions__general_chat_migration
                    (id, user_id, child_id, title, summary_text, summary_until_message_id, created_at, updated_at)
                SELECT id, user_id, child_id, title, summary_text, summary_until_message_id, created_at, updated_at
                FROM chat_sessions
            """)
            connection.exec_driver_sql("DROP TABLE chat_sessions")
            connection.exec_driver_sql(
                "ALTER TABLE chat_sessions__general_chat_migration RENAME TO chat_sessions"
            )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)"
            )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_chat_sessions_child_id ON chat_sessions (child_id)"
            )
            connection.exec_driver_sql("COMMIT")
        except Exception:
            connection.exec_driver_sql("ROLLBACK")
            raise
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            connection.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
