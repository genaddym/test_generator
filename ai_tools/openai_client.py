import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import re
import json
import subprocess
import pickle

OPENAI_MODEL = "gpt-4.1-mini"
#OPENAI_MODEL = "gpt-4-turbo"

MAX_ATTEMPTS = 7

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
    
    def sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize a string to be used as a folder name by removing illegal characters.
        
        Args:
            name (str): Original name
            
        Returns:
            str: Sanitized folder name
        """
        # Remove or replace illegal characters for folder names
        # Illegal characters: < > : " | ? * \ / and control characters
        # Also remove brackets, parentheses, and other problematic characters
        illegal_chars = r'[<>:"|?*\\/#\[\](){}@!$%^&+=;,\'`~]'
        
        # Replace illegal characters with underscores
        sanitized = re.sub(illegal_chars, '_', name)
        
        # Replace multiple consecutive underscores with single underscore
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Remove leading and trailing underscores and dots
        sanitized = sanitized.strip('_.')
        
        # Convert to lowercase
        sanitized = sanitized.lower()
        
        # Ensure it's not empty and doesn't start with a dot
        if not sanitized or sanitized.startswith('.'):
            sanitized = 'folder_' + sanitized.lstrip('.')
        
        # Limit length to avoid filesystem issues
        if len(sanitized) > 200:
            sanitized = sanitized[:200].rstrip('_')
        
        return sanitized

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

    def create_decipher(self, step: dict, test_folder_path: str) -> dict:
        prompt = f"""
        You are a Python network automation expert specializing in CLI command parsing and testing.
        Based on the following step details, extract the CLI command from the step details. 
        Return only the CLI command, no other text.
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": step[step["description_key"]]}
        ]

        print(f"Sending prompt to OpenAI to extract CLI command...")
        self._save_messages(messages)
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.1
        )

        # Extract code from response
        content = response.choices[0].message.content
        print(f"Received response from OpenAI: {content}")
        cli_command = content.strip()
        step["cli_command"] = cli_command
        
        # Create folder name from CLI command if available, otherwise use decipher_id
        folder_name = self.sanitize_folder_name(cli_command)
        command_folder = os.path.join(test_folder_path, folder_name)
        os.makedirs(command_folder, exist_ok=True)

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
        1. The decipher should inherit from Decipher, implement the `decipher` method, 
        extract all the relevant values that are needed for the test step, and return them in a dictionary.
        2. A unit test class that tests the decipher using the provided CLI output. Write a unit test code using the provided CLI output example. Validate that the decipher correctly parses the provided CLI output example.
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

        attempt = 0
        fix_required = False
        
        decipher_file = os.path.join(command_folder, "decipher.py")
        unit_test_file = os.path.join(command_folder, "unit_test.py")
        files_exist = os.path.exists(decipher_file) and os.path.exists(unit_test_file)

        while attempt < MAX_ATTEMPTS:
            if not files_exist or fix_required:
                print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
                self._save_messages(messages)
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
                    
                    Requirements:
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

    def _save_messages(self, messages: list[dict], file_name: str="last_prompt.txt"):
        with open(file_name, "w") as f:
            for message in messages:
                f.write(f"{message['role']}: {message['content']}\n")
        import pudb; pudb.set_trace()

    def create_test_step(self, 
                        zcode_snippets: str, 
                        deciphers_map: dict, 
                        step: dict, 
                        test_file_path: str, 
                        test_file_content: str,
                        previous_steps_description:list[str]) -> dict:
        # Get decipher information if available
        decipher_info = ""
        cli_command = ""
        decipher_class_name = "None"
        if "decipher_id" in step:
            decipher = deciphers_map.get(step["decipher_id"])
            if decipher:
                # Apply input parameters to CLI command if available
                cli_command = decipher['cli_command']
                decipher_class_name = decipher['class_name']

                decipher_info = f"""
                Related Decipher Information:
                - Import: from {decipher['import_path']} import {decipher_class_name}
                - Decipher class name: {decipher_class_name}
                - CLI Command: {cli_command}
                - Expected Output Format: {yaml.dump(decipher.get('json_example', {}), default_flow_style=False)}
                """

        prompt = f"""
        You are a Python network automation expert specializing in test automation.
        
        Based on the following code snippets, step details, and current test file content, implement the test step.
        The implementation should be added to the test method in the test class.
        
        Code Snippets:
        {zcode_snippets}
        
        Current test file content:
        {test_file_content}

        Previous steps:
        {previous_steps_description}
        
        Step details:
        {yaml.dump(step, default_flow_style=False)}
        
        {decipher_info}
        
        Requirements:
        - The implementation must follow the existing test structure
        - Add clear comments explaining the implementation
        - Use the code snippets as reference for implementation patterns
        - If decipher information is provided:
          * Use the import statement to import the decipher class
          * Use the CLI command to execute the command (parameters have been applied)
          * Execute the command and decipher the output using the provided decipher class as follows:
            cli_session = device_manager.cli_sessions[device_name]
            bgp_route = cli_session.send_command(
                command=CLI_COMMAND,
                decipher=DECIPHER_CLASS_NAME,
            )
          * Use the expected output format to validate the results
        - IMPORTANT: Extract the step logic into separate method, if possible
        - IMPORTANT: Add a logger to the beggining of the test step with the step number. Example:
        logger.info(f"Retrieving devices for roles A and Z")

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

        # For debug purposes, save the messages into a file


        attempt = 0
        
        while attempt < MAX_ATTEMPTS:
            print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
            self._save_messages(messages)
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

        with open("code_snippets.py", "r") as f:
            zcode_snippets = f.read()

        guide_file = os.path.join(test_folder_path, "prompt.yml")
        with open(guide_file, "r") as f:
            steps = yaml.safe_load(f)

        # Create test file from template
        test_file_path, test_file_content = self.create_test_file(test_name, test_folder_path)
        
        # Load existing deciphers_map if it exists, otherwise start with empty dict
        import pudb; pu.db

         # TEMPORARY
        deciphers_map_path = os.path.join(test_folder_path, "deciphers_map.pkl")
        if os.path.exists(deciphers_map_path):
            print(f"Loading existing deciphers_map from {deciphers_map_path}")
            with open(deciphers_map_path, "rb") as f:
                deciphers_map = pickle.load(f)
        else:
        # TEMPORARY
            deciphers_map = {}
        
        steps_description = []

        for step in steps:
            import pudb; pudb.set_trace()

            # Prompt the user to continue or skip this step
            print(f"\nProcessing step: {step}")


            # user_input = input("Do you want to process this step? (y to continue, s to skip): ").strip().lower()
            # if user_input == "s":
            #     print("Skipping this step as per user request.")
                
            #     continue

            if "cli_output_example" in step:
                # Generate a decipher_id from the step key (e.g., "step 1" -> "step_1_decipher")
                step_key = list(step.keys())[0]  # Get the first key (e.g., "step 1")
                step["description_key"] = step_key
                decipher_id = f"{step_key.replace(' ', '_')}_decipher"
                step["decipher_id"] = decipher_id
                # decipher = self.create_decipher(step, test_folder_path)
                # deciphers_map[decipher["decipher_id"]] = decipher

            # TEMPORARY
            # Save deciphers_map to a file for later loading/deserialization
            # deciphers_map_path = os.path.join(test_folder_path, "deciphers_map.pkl")
            # with open(deciphers_map_path, "wb") as f:
            #     pickle.dump(deciphers_map, f)
            # TEMPORARY
        
            res = self.create_test_step(zcode_snippets, 
                deciphers_map, 
                step, 
                test_file_path, 
                test_file_content,
                steps_description)

            steps_description.append(res["explanation"])