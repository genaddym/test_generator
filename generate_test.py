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

def main():
    try:
        # Initialize the OpenAI client
        logger.info("Initializing OpenAI client...")
        client = OpenAIClient()
        
        # Path to the test folder containing documentation files
        test_folder = os.path.join("tests", "lab-1", "test_ti_lfa")
        
        # Generate the test implementation
        logger.info(f"Generating test implementation for folder: {test_folder}")
        implementation_guide = client.generate_test(test_folder)
        
        # Print the implementation guide
        print("\nImplementation Guide:")
        print("=" * 80)
        print(implementation_guide)
        print("=" * 80)
        
        logger.info("Test generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 