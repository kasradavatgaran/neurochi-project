
import pandas as pd
from database import SessionLocal, engine
import models
import random
from collections import defaultdict
from pathlib import Path 

GAMES_EXCEL_PATH = "games_data.xlsx"
GAME_IMAGES_DIRECTORY = Path("images") / "game_images"
GAME_IMAGES_URL_PATH = "images/game_images/"

CATEGORY_MAP = {
    1: 'ارتباطات',
    2: 'مهارت های حرکتی درشت',
    3: 'مهارت های حرکتی ریز',
    4: 'حل مسئله',
    5: 'شخصی - اجتماعی'
}


def get_available_game_images():
    """
    پوشه عکس بازی‌ها را اسکن کرده و لیستی از نام فایل‌های موجود را برمی‌گرداند.
    """
    if not GAME_IMAGES_DIRECTORY.is_dir():
        print(f"Warning: Directory not found at '{GAME_IMAGES_DIRECTORY}'")
        return []
    
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    image_files = [f.name for f in GAME_IMAGES_DIRECTORY.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"Warning: No images found in '{GAME_IMAGES_DIRECTORY}'")
    
    return image_files


def seed_games_from_excel():
    db = SessionLocal()
    try:
        print("Synchronizing game classification from the source Excel file...")
        
        available_images = get_available_game_images()
        
        df = pd.read_excel(GAMES_EXCEL_PATH)
        df.dropna(subset=['id', 'title', 'description', 'startDay', 'endDay'], inplace=True)
        existing = db.query(models.Game).all()
        by_source = {game.source_game_id: game for game in existing if game.source_game_id is not None}
        by_content = defaultdict(list)
        for game in existing:
            by_content[(game.title.strip(), game.description.strip(), game.min_age_days, game.max_age_days)].append(game)

        games_added = 0
        for index, row in df.iterrows():
            # gameCategoryId denotes the type of game, not its ASQ skill.
            category_id = int(row['testCategoryId']) if pd.notna(row['testCategoryId']) else -1
            skill_category_name = CATEGORY_MAP.get(category_id, 'عمومی')
            source_id = int(row['id'])
            key = (str(row['title']).strip(), str(row['description']).strip(), int(row['startDay']), int(row['endDay']))
            game = by_source.get(source_id)
            if game is None:
                candidates = [game for game in by_content.get(key, []) if game.source_game_id is None]
                if len(candidates) == 1:
                    game = candidates[0]
                elif len(candidates) > 1:
                    # These source rows have no ASQ classification. It is safe
                    # to remove a legacy guessed skill while retaining both IDs.
                    if skill_category_name == 'عمومی':
                        for candidate in candidates:
                            if candidate.skill_category != 'عمومی':
                                candidate.skill_category = 'عمومی'
                                games_added += 1
                    print(f"Ambiguous legacy source identity {source_id}; record IDs preserved.")
                    continue
            if game is not None:
                if game.source_game_id != source_id or game.skill_category != skill_category_name:
                    game.source_game_id = source_id
                    game.skill_category = skill_category_name
                    games_added += 1
                continue

            image_url_to_save = None
            if available_images:
                random_image_filename = random.choice(available_images)
                image_url_to_save = f"{GAME_IMAGES_URL_PATH}{random_image_filename}"

            new_game = models.Game(
                source_game_id=source_id,
                title=str(row['title']).strip(),
                description=str(row['description']).strip(),
                skill_category=skill_category_name,
                min_age_days=int(row['startDay']),
                max_age_days=int(row['endDay']),
                image_url=image_url_to_save 
            )
            db.add(new_game)
            games_added += 1

        db.commit()
        print(f"{games_added} games have been successfully added to the database.")
        return games_added

    except FileNotFoundError:
        print(f"Error: The file {GAMES_EXCEL_PATH} was not found.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Running games seeder directly...")
    models.Base.metadata.create_all(bind=engine)
    seed_games_from_excel()
    print("Games seeder finished.")
