import os
import sys
import logging
from supabase import create_client, Client
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Supabase connection details
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")


# Setup logging
def setup_logging(console_output=False):
    """
    Configure the logging system.

    Args:
        console_output (bool): Whether to output logs to console (default: False)
    """
    log_filename = f"restaurant_dietary_options.log"

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Always add file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add console handler only if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_filename}")

    # Print message about log file being created even if console logging is disabled
    print(f"Log file created: {log_filename}")

    return logger


# Initial logger setup with default settings
logger = setup_logging(console_output=False)

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Connected to Supabase successfully")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {e}")
    sys.exit(1)


def clear_screen():
    """Clear the terminal screen based on OS."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_restaurants() -> Dict[str, str]:
    """
    Fetch all restaurants from the database and return as a dictionary of name:id.
    """
    logger.info("Fetching restaurants from database")
    response = supabase.table("restaurants").select("id, name").execute()

    if hasattr(response, 'error') and response.error:
        logger.error(f"Error fetching restaurants: {response.error}")
        print(f"Error fetching restaurants: {response.error}")
        return {}

    restaurants = {restaurant['name']: restaurant['id'] for restaurant in response.data}
    logger.info(f"Found {len(restaurants)} restaurants")
    return restaurants


def get_dietary_options() -> Dict[str, str]:
    """
    Fetch all dietary options from the database and return as a dictionary of name:id.
    """
    logger.info("Fetching dietary options from database")
    response = supabase.table("dietary_options").select("id, name").execute()

    if hasattr(response, 'error') and response.error:
        logger.error(f"Error fetching dietary options: {response.error}")
        print(f"Error fetching dietary options: {response.error}")
        return {}

    dietary_options = {option['name']: option['id'] for option in response.data}
    logger.info(f"Found {len(dietary_options)} dietary options")
    return dietary_options


def get_existing_restaurant_dietary_options() -> List[Dict]:
    """
    Fetch existing restaurant-dietary option relationships.
    """
    logger.info("Fetching existing restaurant-dietary option relationships")
    response = supabase.table("restaurant_dietary_options").select("restaurant_id, dietary_option_id").execute()

    if hasattr(response, 'error') and response.error:
        logger.error(f"Error fetching existing relationships: {response.error}")
        print(f"Error fetching existing relationships: {response.error}")
        return []

    logger.info(f"Found {len(response.data)} existing relationships")
    return response.data


def add_dietary_option_to_restaurant(restaurant_id: str, dietary_option_id: str, restaurant_name: str = "",
                                     option_name: str = "") -> bool:
    """
    Add a dietary option to a restaurant in the junction table.
    Returns True if successful, False otherwise.
    """
    # Use names for better logging if provided
    restaurant_log = restaurant_name if restaurant_name else restaurant_id
    option_log = option_name if option_name else dietary_option_id

    logger.info(f"Attempting to associate dietary option '{option_log}' with restaurant '{restaurant_log}'")

    # Check if this relationship already exists
    existing = supabase.table("restaurant_dietary_options") \
        .select("*") \
        .eq("restaurant_id", restaurant_id) \
        .eq("dietary_option_id", dietary_option_id) \
        .execute()

    if hasattr(existing, 'error') and existing.error:
        error_msg = f"Error checking existing relationship: {existing.error}"
        logger.error(error_msg)
        print(error_msg)
        return False

    if existing.data and len(existing.data) > 0:
        logger.info(f"Dietary option '{option_log}' is already associated with restaurant '{restaurant_log}'")
        print("This dietary option is already associated with this restaurant.")
        return False

    # Insert the new relationship
    response = supabase.table("restaurant_dietary_options").insert({
        "restaurant_id": restaurant_id,
        "dietary_option_id": dietary_option_id
    }).execute()

    if hasattr(response, 'error') and response.error:
        error_msg = f"Error adding relationship: {response.error}"
        logger.error(error_msg)
        print(error_msg)
        return False

    logger.info(f"Successfully added dietary option '{option_log}' to restaurant '{restaurant_log}'")
    return True


def display_restaurant_dietary_options(restaurant_id: str, restaurant_name: str, dietary_options: Dict[str, str]):
    """
    Display all dietary options for a specific restaurant.
    """
    logger.info(f"Fetching dietary options for restaurant '{restaurant_name}'")
    response = supabase.table("restaurant_dietary_options") \
        .select("dietary_option_id") \
        .eq("restaurant_id", restaurant_id) \
        .execute()

    if hasattr(response, 'error') and response.error:
        error_msg = f"Error fetching dietary options for restaurant: {response.error}"
        logger.error(error_msg)
        print(error_msg)
        return

    # Create a reverse mapping of id:name for dietary options
    id_to_name = {v: k for k, v in dietary_options.items()}

    print(f"\nCurrent dietary options for {restaurant_name}:")
    if not response.data:
        print("None")
        logger.info(f"Restaurant '{restaurant_name}' has no dietary options")
    else:
        current_options = []
        for item in response.data:
            option_id = item['dietary_option_id']
            if option_id in id_to_name:
                option_name = id_to_name[option_id]
                current_options.append(option_name)
                print(f"- {option_name}")

        logger.info(
            f"Restaurant '{restaurant_name}' has {len(current_options)} dietary options: {', '.join(current_options)}")


def list_all_dietary_options(dietary_options: Dict[str, str]):
    """
    Display all available dietary options.
    """
    print("\nAvailable dietary options:")
    for i, option in enumerate(sorted(dietary_options.keys()), 1):
        print(f"{i}. {option}")


def main():
    """
    Main function that runs the CLI.
    """
    logger.info("Starting Restaurant Dietary Options Manager")
    try:
        # Fetch all restaurants and dietary options once at startup
        restaurants = get_restaurants()
        dietary_options = get_dietary_options()

        if not restaurants:
            logger.error("No restaurants found in the database")
            print("No restaurants found in the database. Please add restaurants first.")
            return

        if not dietary_options:
            logger.error("No dietary options found in the database")
            print("No dietary options found in the database. Please add dietary options first.")
            return

        logger.info(f"Successfully loaded {len(restaurants)} restaurants and {len(dietary_options)} dietary options")
        print(f"Found {len(restaurants)} restaurants and {len(dietary_options)} dietary options.")

        while True:
            clear_screen()
            print("=" * 50)
            print("RESTAURANT DIETARY OPTIONS MANAGER")
            print("=" * 50)

            # Display all restaurants
            print("\nAvailable restaurants:")
            for i, name in enumerate(sorted(restaurants.keys()), 1):
                print(f"{i}. {name}")

            # Get restaurant selection
            print("\nEnter restaurant name or number (or 'exit' to quit):")
            restaurant_input = input("> ").strip()

            if restaurant_input.lower() in ['exit', 'quit', 'q']:
                logger.info("User selected to exit program")
                break

            # Handle numeric input
            if restaurant_input.isdigit():
                idx = int(restaurant_input) - 1
                sorted_names = sorted(restaurants.keys())
                if 0 <= idx < len(sorted_names):
                    logger.info(f"User selected restaurant #{restaurant_input}")
                    restaurant_input = sorted_names[idx]
                    logger.info(f"Translated to restaurant name: '{restaurant_input}'")
                else:
                    logger.warning(f"User provided invalid restaurant number: {restaurant_input}")
                    print(f"Invalid restaurant number. Please enter 1-{len(restaurants)}.")
                    input("Press Enter to continue...")
                    continue

            # Validate restaurant exists
            if restaurant_input not in restaurants:
                logger.warning(f"Restaurant '{restaurant_input}' not found in database")
                print(f"Restaurant '{restaurant_input}' not found.")
                input("Press Enter to continue...")
                continue

            logger.info(f"Selected restaurant: '{restaurant_input}'")

            restaurant_id = restaurants[restaurant_input]

            # Restaurant options loop
            while True:
                clear_screen()
                print(f"Managing dietary options for: {restaurant_input}")

                # Display current dietary options for this restaurant
                display_restaurant_dietary_options(restaurant_id, restaurant_input, dietary_options)

                # Display available options
                list_all_dietary_options(dietary_options)

                print("\nEnter dietary option name or number (or 'done' to go back, 'exit' to quit):")
                option_input = input("> ").strip()

                if option_input.lower() == 'done':
                    logger.info(f"Finished adding options to restaurant '{restaurant_input}'")
                    break
                elif option_input.lower() in ['exit', 'quit', 'q']:
                    logger.info("User chose to exit program")
                    return

                # Handle numeric input
                if option_input.isdigit():
                    idx = int(option_input) - 1
                    sorted_options = sorted(dietary_options.keys())
                    if 0 <= idx < len(sorted_options):
                        logger.info(f"User selected option #{option_input}")
                        option_input = sorted_options[idx]
                        logger.info(f"Translated to option name: '{option_input}'")
                    else:
                        logger.warning(f"User provided invalid option number: {option_input}")
                        print(f"Invalid option number. Please enter 1-{len(dietary_options)}.")
                        input("Press Enter to continue...")
                        continue

                # Validate dietary option exists
                if option_input not in dietary_options:
                    logger.warning(f"Dietary option '{option_input}' not found in database")
                    print(f"Dietary option '{option_input}' not found.")
                    input("Press Enter to continue...")
                    continue

                # Add the relationship
                option_id = dietary_options[option_input]
                if add_dietary_option_to_restaurant(restaurant_id, option_id, restaurant_input, option_input):
                    print(f"Added '{option_input}' to '{restaurant_input}'")
                    logger.info(f"Successfully added '{option_input}' to '{restaurant_input}'")

                input("Press Enter to continue...")

        logger.info("Program completed successfully")
        print("Thank you for using the Restaurant Dietary Options Manager!")
        print(f"A log file has been created with all operations.")

    except KeyboardInterrupt:
        logger.info("Program terminated by user via KeyboardInterrupt")
        print("\nProgram terminated by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        print("Check the log file for more details.")


if __name__ == "__main__":
    # Check if --verbose flag is provided
    console_output = "--verbose" in sys.argv or "-v" in sys.argv

    if console_output:
        # Reinitialize logger with console output enabled
        # Remove existing handlers first
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Setup logger again with console output
        logger = setup_logging(console_output=True)

    main()