"""
Parse an existing prompt file with respect to:
 - YAML format
 - steps structure used to describe network automation prompts
"""

#!/usr/bin/env python3

from pathlib import Path
import logging
from ai_tools.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_NAME = "test_segment_routing_new"

def retrieve_all_prompts():
    """
    Scans the lab1 folder for tests directories that contain prompts.
    """
    tests_directory = Path.cwd().joinpath("tests", "lab1")
    prompts = []
    for test_dir in tests_directory.iterdir():
        if not test_dir.is_dir():
            continue
        prompt_file = test_dir / "prompt.txt"
        if prompt_file.exists():
            prompts.append(test_dir.name)
    return prompts

def main():
    errors = []
    # prompts = retrieve_all_prompts()
    prompts = ["tests_lab1_test_flex_algo_drivenets_Flex_Algo_Automation_Test_DriveNets"]
    for prompt in prompts:
        logger.info(f"Processing prompt: {prompt}")
        try:
            client = OpenAIClient()
            client.convert_prompt(prompt)

            
        except Exception as e:
            logger.error(f"Error generating test: {str(e)}")
            errors.append((prompt, str(e)))
    if errors:
        logger.error("Errors encountered during prompt processing:")
        for prompt, error in errors:
            logger.error(f"Prompt: {prompt}, Error: {error}")

if __name__ == "__main__":
    main() 