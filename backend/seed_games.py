
import pandas as pd
from database import SessionLocal, engine
import models
import random
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
        if db.query(models.Game).count() > 0:
            print("Games table already seeded. Skipping.")
            return

        print("Seeding database with games from Excel file...")
        
        available_images = get_available_game_images()
        
        df = pd.read_excel(GAMES_EXCEL_PATH)
        df.dropna(subset=['title', 'description', 'startDay', 'endDay', 'gameCategoryId'], inplace=True)

        games_added = 0
        for index, row in df.iterrows():
            category_id = int(row['gameCategoryId'])
            skill_category_name = CATEGORY_MAP.get(category_id)

            if not skill_category_name:
                continue

            image_url_to_save = None
            if available_images:
                random_image_filename = random.choice(available_images)
                image_url_to_save = f"{GAME_IMAGES_URL_PATH}{random_image_filename}"

            new_game = models.Game(
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