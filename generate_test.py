#!/usr/bin/env python3

import os
import logging
from ai_tools.openai_client import OpenAIClient
from ai_tools.config import OpenAIClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_NAME = "test_segment_routing"

def main():
    try:
        # Initialize with configuration
        config = OpenAIClientConfig.from_environment()
        client = OpenAIClient(config)
        
        # Generate test and get detailed results
        result = client.generate_test(TEST_NAME)
        
        if result.success:
            logger.info(f"Test generation completed successfully!")
            logger.info(f"Test file: {result.test_file_path}")
            logger.info(f"Generated {len(result.deciphers)} deciphers")
            logger.info(f"Processed {len(result.steps)} steps")
            logger.info(f"Quality score: {result.quality_score}/10")
            logger.info(f"Pylint passed: {result.pylint_passed}")
        else:
            logger.error(f"Test generation failed: {result.error_message}")
            if result.quality_issues:
                logger.error("Quality issues:")
                for issue in result.quality_issues:
                    logger.error(f"  - {issue}")
        
    except Exception as e:
        logger.error(f"Error generating test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 