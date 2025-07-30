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

TEST_NAME = "test_evpn_cin_rr_server_validation_test"

def main():
    try:
        client = OpenAIClient()
        client.generate_test(TEST_NAME)

        
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 