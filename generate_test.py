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
        
        logger.info(f"Generating all test implementations for folder: {test_folder}")
        steps = client.generate_test(test_folder)
        logger.info("Decipher generation completed")
        
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 