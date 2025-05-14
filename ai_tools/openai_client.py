import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import json

OPENAI_MODEL = "gpt-4.1-mini"
# OPENAI_MODEL = "gpt-4-turbo"


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
    
    def _find_md_files(self, test_folder_path: str) -> Tuple[str, str]:
        """
        Find the test flow and command outputs files in the test folder.
        
        Args:
            test_folder_path (str): Path to the test folder
            
        Returns:
            Tuple[str, str]: Paths to test flow and command outputs files
            
        Raises:
            FileNotFoundError: If required files are not found
        """
        md_files = [f for f in os.listdir(test_folder_path) if f.endswith(".md")]
        
        if len(md_files) != 2:
            raise FileNotFoundError(f"Expected exactly 2 .md files in {test_folder_path}, found {len(md_files)}")
        
        command_outputs_file = None
        test_flow_file = None
        
        for file in md_files:
            if "command-outputs" in file.lower():
                command_outputs_file = os.path.join(test_folder_path, file)
            else:
                test_flow_file = os.path.join(test_folder_path, file)
        
        if not command_outputs_file or not test_flow_file:
            raise FileNotFoundError("Could not find both test flow and command outputs files")
        
        return test_flow_file, command_outputs_file
    
    def create_implementation_guide(self, test_folder_path: str) -> None:
        """
        Create an implementation guide based on test documentation and save it to a file.
        
        Args:
            test_folder_path (str): Path to the test folder containing documentation files
        """
        # Read project context
        with open("project_description.txt", "r") as f:
            project_context = f.read()
        
        # Read test template
        template_path = os.path.join("test_template.py")
        with open(template_path, "r") as f:
            test_template = f.read()
        
        # Find test documentation files
        test_flow_file, command_outputs_file = self._find_md_files(test_folder_path)
        
        with open(test_flow_file, "r") as f:
            test_flow = f.read()
        
        with open(command_outputs_file, "r") as f:
            command_outputs = f.read()
        
        prompt = f"""
        Project Context:
        {project_context}

        Test Template:
        {test_template}

        Test Documentation:
        {test_flow}

        Command Outputs:
        {command_outputs}

        Based on the provided project context, test template, and test documentation, generate a list of steps for implementing the test.
        Each step should correspond to a specific CLI command used during the test, and should include:
          - The CLI command being parsed
          - You MUST extract and include a complete example of the CLI command output for this command, taken directly from the provided command outputs file. This is REQUIRED for every step.
          - A description of what needs to be implemented for this command:
             - Provide an example of the full CLI command output. Find the corresponding output in the command outputs file.
             - Specify the required data objects for parsed output.
             - For each CLI command, a folder with the command name should be created. 
            Into this folder, a file called `decipher.py`, file called `data_object.py` and a file called `unit_test.py` should be created.
            - Each decipher should inherit from Decipher.
            - IMPORTANT: Use exact import 'from decipher_base import Decipher' in the decipher file.
            - A unit test should be created in the `unit_test.py` file.
           - Instruct to use the command outputs to create the unit test.
          - Instructions for generating a decipher (including class structure and inheritance)
          - Instructions for generating the required data object(s)
          - Instructions for generating a unit test for the decipher, using the command outputs as examples

        Output the steps as a JSON array, where each element is an object with the following fields:
          - cli_command: The CLI command string
          - cli_output_example: The full example output for this command, extracted from the command outputs file. This field is REQUIRED.
          - description: A brief description of the step.
          - decipher_instructions: Instructions for implementing the decipher
          - data_object_instructions: Instructions for implementing the data object(s)
          - unit_test_instructions: Instructions for implementing the unit test

        The output should be valid JSON, suitable for parsing and further processing in Python.
        """
        
        print("Sending prompt to OpenAI...")
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a network testing expert that helps create test implementations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        print("Received response from OpenAI")
        # Save the implementation guide to a JSON file
        implementation_guide = response.choices[0].message.content
        guide_file = os.path.join(test_folder_path, "implementation_guide.json")
        with open(guide_file, "w") as f:
            f.write(implementation_guide)
    
    def create_deciphers(self, test_folder_path: str, command_id: Optional[str] = None) -> dict:
        """
        For each step in the implementation guide, ask the AI to generate a decipher and unit test,
        then create appropriate folders and files for the implementation. Verify the tests and request
        fixes if needed.
        
        Args:
            test_folder_path (str): Path to the test folder containing the implementation guide
            command_id (Optional[str]): If specified, only generate decipher for this command ID
            
        Returns:
            dict: Dictionary containing test results with the following structure:
                {
                    'passed': [list of passed test paths],
                    'failed': [list of tuples (test_path, failure_details)],
                    'errors': [list of tuples (test_path, error_message)]
                }
        """
        import unittest
        from importlib.machinery import SourceFileLoader
        import sys

        # Read project context
        with open("project_description.txt", "r") as f:
            project_context = f.read()

        guide_file = os.path.join(test_folder_path, "implementation_guide.json")
        with open(guide_file, "r") as f:
            steps = json.load(f)

        # Filter steps if command_id is specified
        if command_id is not None:
            steps = [step for step in steps if step["command_id"] == command_id]
            if not steps:
                raise ValueError(f"No step found with command_id: {command_id}")

        results = {
            'passed': [],
            'failed': [],
            'errors': []
        }

        for step in steps:
            # Create folder name from CLI command
            folder_name = step["cli_command"].replace(" ", "_").replace("/", "_")
            command_folder = os.path.join(test_folder_path, folder_name)
            os.makedirs(command_folder, exist_ok=True)

            # Create class name from folder name
            class_name = ''.join(word.capitalize() for word in folder_name.split('_'))

            # Generate initial implementation
            prompt = f"""
            You are a Python network automation expert specializing in CLI command parsing and testing.
            
            Project Context:
            {project_context}
            
            Based on the following step details, generate two Python files:
            1. A decipher class that inherits from DecipherBase and implements the decipher method
            2. A unit test class that tests the decipher using the provided CLI output
            
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
            - The code must be production-ready and follow Python best practices
            - The code should align with the project context and requirements
            - Do not add any suffixes or prefixes to the class names
            - Do not include any markdown formatting or explanations in the code
            - Do not include any code blocks or backticks
            - The code must be directly executable Python code
            
            IMPORTANT: Your response must contain ONLY the Python code for both files, with no additional text, markdown formatting, or explanations.
            The response should be in this exact format:
            
            # decipher.py
            [Python code for decipher.py]
            
            # unit_test.py
            [Python code for unit_test.py]
            
            Step details:
            {json.dumps(step, indent=2)}
            """
            
            messages = [
                {"role": "system", "content": "You are a Python network automation expert specializing in CLI command parsing and testing. You must respond with only executable Python code, no explanations, markdown, or code blocks."},
                {"role": "user", "content": prompt}
            ]

            max_attempts = 5
            attempt = 0
            while attempt < max_attempts:
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
                
                decipher_code = decipher_part[0].strip()
                unit_test_code = decipher_part[1].strip()
                
                # Save decipher code
                decipher_file = os.path.join(command_folder, "decipher.py")
                with open(decipher_file, "w") as f:
                    f.write(decipher_code)
                
                # Save unit test code
                unit_test_file = os.path.join(command_folder, "unit_test.py")
                with open(unit_test_file, "w") as f:
                    f.write(unit_test_code)

                # Verify the implementation
                try:
                    # Add the test directory to Python path
                    if command_folder not in sys.path:
                        sys.path.append(command_folder)

                    # Load the test module
                    test_module = SourceFileLoader("test_module", unit_test_file).load_module()

                    # Create a test suite and run it
                    suite = unittest.TestLoader().loadTestsFromModule(test_module)
                    test_result = unittest.TestResult()
                    suite.run(test_result)

                    if test_result.wasSuccessful():
                        print(f"\nTest {unit_test_file} PASSED")
                        print(f"Tests run: {test_result.testsRun}")
                        results['passed'].append(unit_test_file)
                        break
                    else:
                        print(f"\nTest {unit_test_file} FAILED")
                        print(f"Tests run: {test_result.testsRun}")
                        print("Failures:")
                        for failure in test_result.failures:
                            print(f"  - {failure[0]}")
                            print(f"    {failure[1]}")
                        print("Errors:")
                        for error in test_result.errors:
                            print(f"  - {error[0]}")
                            print(f"    {error[1]}")
                        
                        error_context = f"""
                        Test {unit_test_file} failed during execution:
                        Tests run: {test_result.testsRun}
                        Failures: {len(test_result.failures)}
                        Errors: {len(test_result.errors)}
                        """
                        for failure in test_result.failures:
                            error_context += f"\nFailure in {failure[0]}:\n{failure[1]}"
                        for error in test_result.errors:
                            error_context += f"\nError in {error[0]}:\n{error[1]}"
                except Exception as e:
                    print(f"\nTest {unit_test_file} ERROR")
                    print(f"Error: {str(e)}")
                    error_context = f"Test {unit_test_file} had an error: {str(e)}"

                # If we got here, the test failed or had an error
                if attempt < max_attempts - 1:
                    # Add the error context to the messages for the next attempt
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"""
                        The previous implementation had issues:
                        {error_context}
                        
                        Please provide a fixed version of both files that addresses these issues.
                        Keep the same class names and ensure the code is directly executable.
                        """
                    })
                    attempt += 1
                else:
                    if test_result.wasSuccessful():
                        results['passed'].append(unit_test_file)
                    else:
                        results['failed'].append((unit_test_file, error_context))
                    break

        return results

    def verify_unit_tests(self, test_paths: list) -> dict:
        """
        Execute the unit tests and return their results.
        
        Args:
            test_paths (list): List of paths to unit test files
            
        Returns:
            dict: Dictionary containing test results with the following structure:
                {
                    'passed': [list of passed test paths],
                    'failed': [list of failed test paths],
                    'errors': [list of test paths with errors]
                }
        """
        import unittest
        from importlib.machinery import SourceFileLoader
        import sys
        import os

        results = {
            'passed': [],
            'failed': [],
            'errors': []
        }

        for test_path in test_paths:
            try:
                # Add the test directory to Python path
                test_dir = os.path.dirname(test_path)
                if test_dir not in sys.path:
                    sys.path.append(test_dir)

                # Load the test module
                test_module = SourceFileLoader("test_module", test_path).load_module()

                # Create a test suite and run it
                suite = unittest.TestLoader().loadTestsFromModule(test_module)
                test_result = unittest.TestResult()
                suite.run(test_result)

                if test_result.wasSuccessful():
                    results['passed'].append(test_path)
                else:
                    results['failed'].append(test_path)
            except Exception as e:
                results['errors'].append((test_path, str(e)))

        return results

    def generate_test(self, test_folder_path: str, command_id: Optional[str] = None) -> str:
        """
        Generate test implementation and return the implementation guide content.
        
        Args:
            test_folder_path (str): Path to the test folder containing documentation files
            
        Returns:
            str: Generated implementation instructions
        """
        # self.create_implementation_guide(test_folder_path)
        self.create_deciphers(test_folder_path, command_id=command_id)
