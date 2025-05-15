import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import importlib.util
import sys
import re
import json
import pytest
from io import StringIO
import sys
import subprocess

OPENAI_MODEL = "gpt-4.1-mini"
#OPENAI_MODEL = "gpt-4-turbo"


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (Optional[str]): OpenAI API key. If not provided, will try to load from .env file
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it or set it in .env file")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def run_pytest(self, test_file: str) -> Tuple[int, str]:
        """
        Run pytest in a subprocess and capture its output.
        
        Args:
            test_file (str): Path to the test file
            
        Returns:
            Tuple[int, str]: (exit_code, output)
        """
        # Add the project root to Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = project_root

        # Run pytest in a subprocess
        result = subprocess.run(
            ["pytest", str(test_file), "-vv"],
            capture_output=True,
            text=True,
            env=env
        )
        
        return result.returncode, result.stdout + result.stderr

    def create_deciphers(self, test_folder_path: str, command_id: Optional[str] = None) -> dict:
        """
        For each step in the implementation guide, ask the AI to generate a decipher and unit test,
        then create appropriate folders and files for the implementation. Verify the tests and request
        fixes if needed.
        
        Args:
            test_folder_path (str): Path to the test folder containing the implementation guide
            command_id (Optional[str]): If specified, only generate decipher for this command ID
            
        Returns:
            dict: Dictionary containing the steps with additional metadata:
                {
                    'steps': [
                        {
                            'command_id': str,
                            'cli_command': str,
                            'cli_output_example': str,
                            'decipher_instructions': str,
                            'unit_test_instructions': str,
                            'class_name': str,  # The generated class name
                            'import_path': str,  # The import path for the decipher
                            'json_example': dict  # Example JSON output from the unit test
                        },
                        ...
                    ]
                }
        """

        # Read project context
        with open("project_description.txt", "r") as f:
            project_context = f.read()

        guide_file = os.path.join(test_folder_path, "implementation_guide.yml")
        with open(guide_file, "r") as f:
            steps = yaml.safe_load(f)

        # Filter steps if command_id is specified
        if command_id is not None:
            steps = [step for step in steps if step["command_id"] == command_id]
            if not steps:
                raise ValueError(f"No step found with command_id: {command_id}")

        for step in steps:
            step["unit_test_instructions"] = "Write a unit test code using the provided CLI output example. Validate that the decipher correctly parses the provided CLI output example."

            if "decipher_instructions" in step:
                step["decipher_instructions"] = "The decipher should inherit from Decipher, implement the `decipher` method, and " + step["decipher_instructions"]

            # Create folder name from CLI command
            folder_name = step["cli_command"].replace(" ", "_").replace("/", "_")
            command_folder = os.path.join(test_folder_path, folder_name)
            os.makedirs(command_folder, exist_ok=True)

            # Create class name from folder name
            class_name = ''.join(word.capitalize() for word in folder_name.split('_'))
            step["class_name"] = f"{class_name}Decipher"
            
            # Create import path
            relative_path = os.path.relpath(command_folder, test_folder_path)
            import_path = relative_path.replace(os.path.sep, '.')
            step["import_path"] = f"{import_path}.decipher"

            # Generate initial implementation
            prompt = f"""
            You are a Python network automation expert specializing in CLI command parsing and testing.
            
            Project Context:
            {project_context}
            
            Based on the following step details, generate three sections:
            1. A decipher class that inherits from DecipherBase and implements the decipher method
            2. A unit test class that tests the decipher using the provided CLI output
            3. An explanation of the implementation and any important design decisions
            
            Requirements:
            - The decipher class must be named '{class_name}Decipher'. All non-alphanumeric characters should be removed.
            - The class name must use CamelCase format (e.g., 'ShowVersionDecipher' not 'Show-version-decipher')
            - All JSON keys must use underscores instead of hyphens (e.g., 'command_output' not 'command-output')
            - The decipher method must be defined exactly as: '@staticmethod def decipher(cli_response: str)'
            - The decipher must implement the decipher method
            - The unit test class must be named exactly 'Test{class_name}Decipher'
            - The unit test must use the provided CLI output example
            - Unit tests must use pytest framework (not unittest)
            - Both files must be properly formatted with imports and docstrings
            - The class docstring must include the CLI command being parsed (e.g., 'Parser for "show version" command')
            - The code must align with the project context and requirements
            - Do not add any suffixes or prefixes to the class names
            - Do not include any markdown formatting or explanations in the code
            - Do not include any code blocks or backticks
            - The code must be directly executable Python code
            - IMPORTANT: In the unit test, define the expected output as a single line variable named 'expected_output' with a valid JSON string
            - Example of expected_output format: expected_output = {{"key": "value", "nested": {{"key": "value"}}}}
            - IMPORTANT: In the unit test file, use relative imports for importing the decipher class (e.g., 'from .decipher import ShowLldpNeighborsDecipher')
            - IMPORTANT: In the decipher file, import the base class using 'from tests.base.decipher import Decipher'
            
            Your response must be in this exact format:
            
            # decipher.py
            [Python code for decipher.py]
            
            # unit_test.py
            [Python code for unit_test.py]
            
            # explanation
            [Short summary of your recent changes]
            
            Step details:
            {yaml.dump(step, default_flow_style=False)}
            """
            
            messages = [
                {"role": "system", "content": "You are a Python network automation expert specializing in CLI command parsing and testing. You must respond with executable Python code and explanations in the specified format."},
                {"role": "user", "content": prompt}
            ]

            max_attempts = 5
            attempt = 0
            fix_required = False
            while attempt < max_attempts:
                # Check if decipher file already exists
                decipher_file = os.path.join(command_folder, "decipher.py")
                unit_test_file = os.path.join(command_folder, "unit_test.py")
                files_exist = os.path.exists(decipher_file) and os.path.exists(unit_test_file)

                if not files_exist or fix_required:
                    print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {max_attempts}")
                    response = self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=messages,
                        temperature=0.1
                    )
                    print("Received response from OpenAI")
                    # Extract code from response
                    content = response.choices[0].message.content
                    
                    # Split into files using the file markers
                    parts = content.split("# decipher.py")
                    if len(parts) != 2:
                        raise ValueError("AI response did not contain decipher.py marker")
                    
                    decipher_part = parts[1].split("# unit_test.py")
                    if len(decipher_part) != 2:
                        raise ValueError("AI response did not contain unit_test.py marker")
                    
                    unit_test_part = decipher_part[1].split("# explanation")
                    if len(unit_test_part) != 2:
                        raise ValueError("AI response did not contain explanation marker")
                    
                    decipher_code = decipher_part[0].strip()
                    unit_test_code = unit_test_part[0].strip()
                    explanation = unit_test_part[1].strip()
                    
                    # Log the explanation
                    print("\nImplementation Explanation:")
                    print("=" * 80)
                    print(explanation)
                    print("=" * 80)
                    
                    # Save decipher code
                    with open(decipher_file, "w") as f:
                        f.write(decipher_code)
                    
                    # Save unit test code
                    with open(unit_test_file, "w") as f:
                        f.write(unit_test_code)
                else:
                    print(f"\nSkipping OpenAI call - using existing files in {command_folder}")

                # Verify the implementation
                try:
                    # Run pytest in a subprocess
                    exit_code, test_output = self.run_pytest(unit_test_file)
                    
                    if exit_code == 0:
                        print(f"\nTest {unit_test_file} PASSED")
                        fix_required = False
                        # Read the test file to extract JSON example
                        with open(unit_test_file, 'r') as f:
                            test_content = f.read()
                        json_example_match = re.search(r'expected_output\s*=\s*({[^{}]*(?:{[^{}]*}[^{}]*)*})', test_content)
                        if json_example_match:
                            try:
                                json_example = json.loads(json_example_match.group(1))
                                step["json_example"] = json_example
                            except json.JSONDecodeError as e:
                                print(f"Warning: Could not parse JSON example from unit test for {step['command_id']}: {str(e)}")
                                print(f"Captured JSON: {json_example_match.group(1)}")
                        break
                    else:
                        print(f"\nTest {unit_test_file} FAILED")
                        error_context = f"""
                        Test {unit_test_file} failed with exit code {exit_code}
                        
                        Test Output:
                        {test_output}
                        """
                        fix_required = True
                except Exception as e:
                    print(f"\nTest {unit_test_file} ERROR")
                    print(f"Error: {str(e)}")
                    error_context = f"Test {unit_test_file} had an error: {str(e)}"
                    fix_required = True

                # If we got here, the test failed or had an error
                if attempt < max_attempts - 1:
                    # Add the error context to the messages for the next attempt
                    if files_exist:
                        # If files exist, we need to read their content for the next attempt
                        with open(decipher_file, 'r') as f:
                            decipher_code = f.read()
                        with open(unit_test_file, 'r') as f:
                            unit_test_code = f.read()
                        content = f"# decipher.py\n{decipher_code}\n# unit_test.py\n{unit_test_code}"
                    else:
                        # If files were just generated, use the code we already have
                        content = f"# decipher.py\n{decipher_code}\n# unit_test.py\n{unit_test_code}"
                    
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"""
                        The previous implementation had issues:
                        {error_context}
                        
                        Please provide a fixed version of both files that addresses these issues.
                        Keep the same class names and ensure the code is directly executable.
                        Remember to define expected_output as a single line variable with a valid JSON string.
                        
                        Original requirements:
                        - The decipher class must be named '{step["class_name"]}'
                        - The class must inherit from DecipherBase
                        - The decipher method must be defined exactly as: '@staticmethod def decipher(cli_response: str)'
                        - The unit test class must be named exactly 'Test{step["class_name"]}'
                        - The unit test must use the provided CLI output example
                        - Unit tests must use pytest framework
                        - Both files must be properly formatted with imports and docstrings
                        - The class docstring must include the CLI command being parsed
                        - The code must be production-ready and follow Python best practices
                        - In the unit test, define the expected output as a single line variable named 'expected_output' with a valid JSON string
                        - In the unit test file, use relative imports for importing the decipher class
                        - In the decipher file, import the base class using 'from tests.base.decipher import Decipher'
                        
                        CLI Output Example:
                        {step["cli_output_example"]}
                        
                        Decipher Instructions:
                        {step["decipher_instructions"]}
                        
                        Unit Test Instructions:
                        {step["unit_test_instructions"]}
                        """
                    })
                    attempt += 1
                else:
                    break

        return {'steps': steps}
       

    def generate_test(self, test_folder_path: str, command_id: Optional[str] = None) -> str:
        self.create_deciphers(test_folder_path, command_id=command_id)
