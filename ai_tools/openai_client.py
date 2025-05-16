import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import re
import json
import subprocess

OPENAI_MODEL = "gpt-4.1-mini"
#OPENAI_MODEL = "gpt-4-turbo"

MAX_ATTEMPTS = 5

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

    def create_decipher(self, step: dict, command_folder: str) -> dict:
        """
        Generate a decipher and unit test for a single step, then verify the implementation.
        
        Args:
            step (dict): Step details containing command_id, cli_command, cli_output_example, etc.
            command_folder (str): Path to the folder where decipher and test files should be created
            
        Returns:
            dict: Updated step dictionary with additional metadata
        """
        # Create class name from folder name
        folder_name = os.path.basename(command_folder)
        class_name = ''.join(word.capitalize() for word in folder_name.split('_'))
        step["class_name"] = f"{class_name}Decipher"
        
        # Create import path
        relative_path = os.path.relpath(command_folder, os.path.dirname(command_folder))
        import_path = relative_path.replace(os.path.sep, '.')
        step["import_path"] = f"{import_path}.decipher"

        # Generate initial implementation
        prompt = f"""
        You are a Python network automation expert specializing in CLI command parsing and testing.
        
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

        MAX_ATTEMPTS = 5
        attempt = 0
        fix_required = False
        
        decipher_file = os.path.join(command_folder, "decipher.py")
        unit_test_file = os.path.join(command_folder, "unit_test.py")
        files_exist = os.path.exists(decipher_file) and os.path.exists(unit_test_file)

        while attempt < MAX_ATTEMPTS:
            if not files_exist or fix_required:
                print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
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
                    messages.append({
                        "role": "user",
                        "content": "Your response is missing the '# decipher.py' marker. Please provide the response in the correct format with all required sections: # decipher.py, # unit_test.py, and # explanation."
                    })
                    continue
                
                decipher_part = parts[1].split("# unit_test.py")
                if len(decipher_part) != 2:
                    messages.append({
                        "role": "user",
                        "content": "Your response is missing the '# unit_test.py' marker. Please provide the response in the correct format with all required sections: # decipher.py, # unit_test.py, and # explanation."
                    })
                    continue
                
                unit_test_part = decipher_part[1].split("# explanation")
                if len(unit_test_part) != 2:
                    messages.append({
                        "role": "user",
                        "content": "Your response is missing the '# explanation' marker. Please provide the response in the correct format with all required sections: # decipher.py, # unit_test.py, and # explanation."
                    })
                    continue
                
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
                    return step
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
            if attempt < MAX_ATTEMPTS - 1:
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

        return step
       
    def create_test_file(self, test_name: str, test_folder_path: str) -> tuple[str, str]:
        """
        Create a new test file from template with proper class and method names.
        If file exists, read and return its content.
        
        Args:
            test_name (str): Name of the test (e.g., 'show_lldp_neighbors')
            test_folder_path (str): Path to the test folder
            
        Returns:
            tuple[str, str]: Path to the test file and its content
        """
        test_file = os.path.join(test_folder_path, f"{test_name}.py")
        if os.path.exists(test_file):
            # Read existing file content
            with open(test_file, "r") as f:
                template_content = f.read()
        else:
            # Read the template
            with open("test_template.py", "r") as f:
                template_content = f.read()
            
            # Convert test_name to camel case for class name
            class_name = ''.join(word.capitalize() for word in test_name.split('_'))
            
            # Replace class and method names
            template_content = template_content.replace("class TestTemplate", f"class Test{class_name}")
            template_content = template_content.replace("def test_template", f"def {test_name}")
            
            # Write the modified template to the test file
            with open(test_file, "w") as f:
                f.write(template_content)
        
        return test_file, template_content

    def create_test_step(self, project_context: str, code_snippets: str, deciphers_map: dict, step: dict, test_file_path: str, test_file_content: str, input_parameters: dict = None) -> dict:
        """
        Generate a test step implementation using AI.
        
        Args:
            project_context (str): Project context from project_description.txt
            code_snippets (str): Code snippets from code_snippets.py
            deciphers_map (dict): Map of decipher_id to decipher details
            step (dict): Step details from implementation_guide.yml
            test_file_path (str): Path to the test file
            test_file_content (str): Current content of the test file
            input_parameters (dict, optional): Parameters to be applied to CLI commands
        """
        # Get decipher information if available
        decipher_info = ""
        if "related_decipher_id" in step:
            decipher = deciphers_map.get(step["related_decipher_id"])
            if decipher:
                # Apply input parameters to CLI command if available
                cli_command = decipher['cli_command']
                if input_parameters and "input_parameters" in decipher:
                    for param in decipher["input_parameters"]:
                        if param in input_parameters:
                            cli_command = cli_command.replace(param, str(input_parameters[param]))

                decipher_info = f"""
                Related Decipher Information:
                - Import: from {decipher['import_path']} import {decipher['class_name']}
                - Decipher class name: {decipher['class_name']}
                - CLI Command: {cli_command}
                - Expected Output Format: {yaml.dump(decipher.get('json_example', {}), default_flow_style=False)}
                """

        prompt = f"""
        You are a Python network automation expert specializing in test automation.
        
        Based on the following project context, code snippets, step details, and current test file content, implement the test step.
        The implementation should be added to the test method in the test class.
        
        Project Context:
        {project_context}
        
        Code Snippets:
        {code_snippets}
        
        Current test file content:
        {test_file_content}
        
        Step details:
        {yaml.dump(step, default_flow_style=False)}
        
        {decipher_info}
        
        Requirements:
        - The implementation must follow the existing test structure
        - Add clear comments explaining the implementation
        - Use the project context and code snippets as reference for implementation patterns
        - If decipher information is provided:
          * Use the import statement to import the decipher class
          * Use the CLI command to execute the command (parameters have been applied)
          * Execute the command and decipher the output using the provided decipher class as follows:
            cli_session = device_manager.cli_sessions[device_name]
            bgp_route = cli_session.send_command(
                command=f"{cli_command}",
                decipher={decipher['class_name']},
            )
          * Use the expected output format to validate the results
        - Find a comment # Step implementation completed. This is the previous implementation of the test step. Remove this comment and start implementing the new step from this point, if applicable.
        - At the end of the test step, insert a comment with the following format:
        # Step implementation completed

        IMPORTANT: Your response must be in this exact format:
        
        # new_file_content
        [Complete updated test file content]
        
        # explanation
        [Explanation of changes made]
        """
        
        messages = [
            {"role": "system", "content": "You are a Python network automation expert specializing in test automation. You must respond with executable Python code that follows the project's structure and standards."},
            {"role": "user", "content": prompt}
        ]

        attempt = 0
        
        while attempt < MAX_ATTEMPTS:
            print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.1
            )
            print("Received response from OpenAI")
            
            # Extract code from response
            content = response.choices[0].message.content
            
            # Split into new file content and explanation
            parts = content.split("# new_file_content")
            if len(parts) != 2:
                messages.append({
                    "role": "user",
                    "content": "Your response is missing the '# new_file_content' marker. Please provide the response in the correct format with new file content and explanation sections."
                })
                attempt += 1
                continue
            
            file_content_part = parts[1].split("# explanation")
            if len(file_content_part) != 2:
                messages.append({
                    "role": "user",
                    "content": "Your response is missing the '# explanation' marker. Please provide the response in the correct format with new file content and explanation sections."
                })
                attempt += 1
                continue
            
            new_file_content = file_content_part[0].strip()
            explanation = file_content_part[1].strip()
            
            # Log the explanation
            print("\nImplementation Explanation:")
            print("=" * 80)
            print(explanation)
            print("=" * 80)
            
            # Write the new file content
            with open(test_file_path, "w") as f:
                f.write(new_file_content)
            
            step["test_file_content"] = new_file_content
            step["explanation"] = explanation
            return step

        return step

    def generate_test(self, test_name: str):
        test_folder_path = os.path.join("tests", "lab1", test_name)
        with open("project_description.txt", "r") as f:
            project_context = f.read()

        with open("code_snippets.py", "r") as f:
            code_snippets = f.read()

        guide_file = os.path.join(test_folder_path, "implementation_guide.yml")
        with open(guide_file, "r") as f:
            steps = yaml.safe_load(f)

        # Create test file from template
        test_file_path, test_file_content = self.create_test_file(test_name, test_folder_path)

        # 1. create deciphers
        # Filter steps to only include those with decipher_id
        deciphers = [step for step in steps if "decipher_id" in step]
        deciphers_map = {decipher["decipher_id"]: decipher for decipher in deciphers}

        for decipher in deciphers:
            decipher["unit_test_instructions"] = "Write a unit test code using the provided CLI output example. Validate that the decipher correctly parses the provided CLI output example."

            if "decipher_instructions" in decipher:
                decipher["decipher_instructions"] = "The decipher should inherit from Decipher, implement the `decipher` method, and " + decipher["decipher_instructions"]

            # Create folder name from CLI command
            folder_name = decipher["cli_command"].replace(" ", "_").replace("/", "_")
            command_folder = os.path.join(test_folder_path, folder_name)
            os.makedirs(command_folder, exist_ok=True)

            # Create decipher
            decipher = self.create_decipher(decipher, command_folder)

        # Update the implementation_guide file with the deciphers
        with open(guide_file, "w") as f:
            yaml.dump(deciphers, f)

        # 2. create the test steps
        # Filter steps to only include those with step_id
        steps = [step for step in steps if "step_id" in step]

        for step in steps:
            step = self.create_test_step(project_context, code_snippets, deciphers_map, step, test_file_path, test_file_content)

