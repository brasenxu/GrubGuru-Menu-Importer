import os
import json
from supabase import create_client
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("menu_import.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found in .env file")
    raise ValueError("Missing Supabase credentials. Please check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MENU_DIR = os.getenv("MENU_DIR")

def get_json_files(directory):
    json_files = []
    for file in os.listdir(directory):
        if file.endswith(".json"):
            json_files.append(file)
    return json_files

def extract_restaurant_name(filename):
    return os.path.splitext(filename)[0]

def load_menu_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError:
        logger.error(f"Error parsing JSON file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None


def update_restaurant_menu(restaurant_name, menu_data):
    try:
        # Check if the restaurant exists
        result = (
            supabase.table("restaurants")
            .select("id")
            .eq("name", restaurant_name)
            .execute()
        )

        if not result.data:
            logger.warning(f"No restaurant found with name: {restaurant_name}")
            return False

        update_result = (
            supabase.table("restaurants")
            .update({"menus": menu_data})
            .eq("name", restaurant_name)
            .execute()
        )

        if update_result.data:
            logger.info(f"Successfully updated menu for {restaurant_name}")
            return True
        else:
            logger.warning(f"Update operation returned no data for {restaurant_name}")
            return False

    except Exception as e:
        logger.error(f"Error updating restaurant {restaurant_name}: {str(e)}")
        return False

def main():
    json_files = get_json_files(MENU_DIR)
    logger.info(f"Found {len(json_files)} JSON files to process")

    success_count = 0
    failure = 0

    for json_file in json_files:
        restaurant_name = extract_restaurant_name(json_file)
        file_path = os.path.join(MENU_DIR, json_file)
        logger.info(f"Processing {restaurant_name} from {file_path}")

        menu_data = load_menu_data(file_path)
        if menu_data is None:
            logger.error(f"Skipping {restaurant_name} due to data loading error")
            failure += 1
            continue

        success = update_restaurant_menu(restaurant_name, menu_data)
        if success:
            success_count += 1
        else:
            failure += 1

    logger.info(f"Import complete. Successful: {success_count}, Failed: {failure}")


if __name__ == "__main__":
    main()

