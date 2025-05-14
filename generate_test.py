#!/usr/bin/env python3

import os
import logging
from ai_tools.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_NAME = "test_conditional_advertisement_legacy"

def get_user_choice() -> tuple[bool, str | None]:
    """
    Ask user if they want to generate all tests or a specific decipher.
    
    Returns:
        tuple[bool, str | None]: (is_full_test, command_id)
            - is_full_test: True if generating all tests, False if specific decipher
            - command_id: The command ID if generating specific decipher, None otherwise
    """
    while True:
        print("\nWhat would you like to generate?")
        print("1. All tests")
        print("2. Specific decipher")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "1":
            return True, None
        elif choice == "2":
            command_id = input("Enter the command ID: ").strip()
            if not command_id:
                print("Command ID cannot be empty. Please try again.")
                continue
            return False, command_id
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    try:
        # Initialize the OpenAI client
        logger.info("Initializing OpenAI client...")
        client = OpenAIClient()
        
        # Path to the test folder containing documentation files
        test_folder = os.path.join("tests", "lab1", TEST_NAME)
        
        # Get user's choice
        is_full_test, command_id = get_user_choice()
        
        # Generate the test implementation
        if is_full_test:
            logger.info(f"Generating all test implementations for folder: {test_folder}")
            results = client.create_deciphers(test_folder)
        else:
            logger.info(f"Generating decipher for command ID {command_id} in folder: {test_folder}")
            results = client.create_deciphers(test_folder, command_id=command_id)
        
        # Print the results
        print("\nTest Results:")
        print("=" * 80)
        if results['passed']:
            print(f"\nPassed tests ({len(results['passed'])}):")
            for test in results['passed']:
                print(f"  ✓ {test}")
        
        if results['failed']:
            print(f"\nFailed tests ({len(results['failed'])}):")
            for test, details in results['failed']:
                print(f"  ✗ {test}")
                print(f"    Details: {details}")
        
        if results['errors']:
            print(f"\nTests with errors ({len(results['errors'])}):")
            for test, error in results['errors']:
                print(f"  ! {test}")
                print(f"    Error: {error}")
        print("=" * 80)
        
        logger.info("Test generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 