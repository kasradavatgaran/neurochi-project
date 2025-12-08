
import pandas as pd
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
import sys

CSV_PATH = "Test_anser_book.csv"
IMAGE_BASE_PATH = "images/test_images/"

def seed_database_from_csv():
    db = SessionLocal()
    try:
        if db.query(models.Question).count() > 0:
            print("Database already seeded. Skipping CSV loading.")
            return

        print("Seeding database from CSV file...")
        
        column_names = ['id', 'question', 'start_day', 'end_day', 'category', 'filename']
        
        df = pd.read_csv(
            CSV_PATH, 
            header=0, 
            names=column_names, 
            engine='python',
            sep=',',
            skipinitialspace=True 
        )


        df['category'] = df['category'].str.strip().str.strip("'\"")
        df['question'] = df['question'].str.strip().str.strip("'\"")


        df.dropna(subset=['category', 'start_day', 'end_day', 'id'], inplace=True)

        for col in ['id', 'start_day', 'end_day']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(subset=['id', 'start_day', 'end_day'], inplace=True)
        df[['id', 'start_day', 'end_day']] = df[['id', 'start_day', 'end_day']].astype(int)
        
        unique_sets = df.groupby(['category', 'start_day', 'end_day']).size().reset_index(name='count')
        set_map = {}

        for index, row in unique_sets.iterrows():
            category = row['category']
            min_age = int(row['start_day'])
            max_age = int(row['end_day'])
            
            set_name = f"{category}_{min_age}-{max_age}_days"

            new_set = models.SkillQuestionSet(name=set_name, skill_category=category, min_age_days=min_age, max_age_days=max_age)
            db.add(new_set)
            db.flush()
            set_map[(category, min_age, max_age)] = new_set.id

        print(f"{len(set_map)} unique question sets created.")

        question_counter = 0
        for index, row in df.iterrows():
            key = (row['category'], int(row['start_day']), int(row['end_day']))
            set_id = set_map.get(key)
            
            if set_id:
                new_question = models.Question(
                    question_set_id=set_id,
                    order_index=int(row['id']),
                    text=str(row['question']),
                    image_url=f"{IMAGE_BASE_PATH}{row['filename']}" if pd.notna(row['filename']) else None,
                    option_A="بله", score_A=10.0,
                    option_B="گاهی", score_B=5.0,
                    option_C="هنوز نه", score_C=0.0
                )
                db.add(new_question)
                question_counter += 1
            else:
                print(f"WARNING: Could not find a matching question set for row {index + 2}.")

        db.commit()
        print(f"{question_counter} questions have been added to the database successfully.")

    except Exception as e:
        db.rollback()
        print(f"\nAN ERROR OCCURRED: {e}")
        print("Database transaction rolled back.")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("Running seeder directly...")
    models.Base.metadata.create_all(bind=engine)
    seed_database_from_csv()
    print("Seeder finished.")