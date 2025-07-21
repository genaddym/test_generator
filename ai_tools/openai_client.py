import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import re
import json
import subprocess
import pickle

OPENAI_MODEL = "gpt-4.1"


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
        prompt = self._create_structured_prompt(
            role="Python network automation expert specializing in CLI command parsing and testing",
            task="Extract the CLI command from the provided step details.",
            requirements=[
                "MUST return only the CLI command text",
                "MUST NOT include any explanations or additional text",
                "MUST extract the exact command that needs to be executed"
            ],
            context={
                "step_details": step[step["description_key"]]
            }
        )

        messages = [
            {"role": "system", "content": "You are a Python network automation expert specializing in CLI command parsing and testing."},
            {"role": "user", "content": prompt}
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
        if not content:
            raise ValueError("OpenAI returned empty response for CLI command extraction")
        print(f"Received response from OpenAI: {content}")
        cli_command = content.strip()
        step["cli_command"] = cli_command
        
        # Create folder name from CLI command if available, otherwise use decipher_id
        folder_name = self.sanitize_folder_name(cli_command)
        command_folder = os.path.join(test_folder_path, folder_name)
        os.makedirs(command_folder, exist_ok=True)

        # Create pickle filename based on decipher_id for caching in the command folder
        decipher_id = step.get("decipher_id", "unknown_decipher")
        decipher_pickle_file = os.path.join(command_folder, f"{decipher_id}.pkl")
        
        # Check if cached decipher exists in the command folder
        if os.path.exists(decipher_pickle_file):
            print(f"Loading cached decipher from {decipher_pickle_file}")
            try:
                with open(decipher_pickle_file, "rb") as f:
                    cached_step = pickle.load(f)
                print(f"Successfully loaded cached decipher: {cached_step.get('class_name', 'Unknown')}")
                return cached_step
            except Exception as e:
                print(f"Failed to load cached decipher from {decipher_pickle_file}: {e}")
                print("Proceeding with fresh decipher generation...")

        class_name = ''.join(word.capitalize() for word in folder_name.split('_'))
        step["class_name"] = f"{class_name}Decipher"
        
        # Create import path
        relative_path = os.path.relpath(command_folder, os.path.dirname(command_folder))
        import_path = relative_path.replace(os.path.sep, '.')
        step["import_path"] = f"{import_path}.decipher"

        # Generate initial implementation using structured prompt
        prompt = self._create_structured_prompt(
            role="Python network automation expert specializing in CLI command parsing and testing",
            task=f"Generate a decipher class named '{class_name}Decipher' and corresponding unit test to parse CLI command output and extract relevant data for test automation.",
            requirements=[
                f"MUST name the decipher class exactly '{class_name}Decipher' (CamelCase, no extra suffixes)",
                "MUST inherit from Decipher base class",
                "MUST implement exactly: '@staticmethod def decipher(cli_response: str)'",
                f"MUST name unit test class exactly 'Test{class_name}Decipher'",
                "MUST use pytest framework (not unittest)",
                "MUST use underscores for JSON keys (not hyphens): 'command_output' not 'command-output'",
                "MUST define expected_output as single line variable with valid JSON string",
                "MUST use relative imports in unit test: 'from decipher import {class_name}Decipher'",
                "MUST import base class: 'from tests.base.decipher import Decipher'",
                "MUST include CLI command in class docstring",
                "MUST write directly executable Python code (no markdown/backticks)",
                "MUST format both files with proper imports and docstrings",
                "MUST validate decipher correctly parses the provided CLI output example"
            ],
            context={
                "cli_command": cli_command,
                "step_details": yaml.dump(step, default_flow_style=False),
                "class_name": class_name
            },
            output_format="""
# decipher.py
[Python code for decipher.py]

# unit_test.py
[Python code for unit_test.py]

# explanation
[Short summary of implementation and design decisions]
"""
        )
        
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
                if not content:
                    messages.append({
                        "role": "user",
                        "content": "OpenAI returned empty response. Please provide the response in the correct format with all required sections: # decipher.py, # unit_test.py, and # explanation."
                    })
                    continue
                
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
                    
                    # Cache the successfully created decipher for future use
                    try:
                        with open(decipher_pickle_file, "wb") as f:
                            pickle.dump(step, f)
                        print(f"Successfully cached decipher to {decipher_pickle_file}")
                    except Exception as e:
                        print(f"Warning: Failed to cache decipher to {decipher_pickle_file}: {e}")
                    
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
                    - In the unit test file, use relative imports for importing the decipher class, without using the . before decipher. Example: 'from decipher import ShowIsisNeighborsIncRoleZDecipher'. Using . before decipher will cause ImportError.
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

    def _create_structured_prompt(self, 
                                 role: str,
                                 task: str, 
                                 requirements: list[str],
                                 context: Optional[dict] = None,
                                 examples: Optional[str] = None,
                                 output_format: Optional[str] = None) -> str:
        """
        Create a well-structured prompt for AI that's easy to understand.
        
        Args:
            role: The role the AI should take (e.g., "Python network automation expert")
            task: The main task description
            requirements: List of specific requirements
            context: Dictionary of context information (optional)
            examples: Example content (optional)  
            output_format: Expected output format (optional)
        """
        sections = []
        
        # Role definition
        sections.append(f"You are a {role}.")
        sections.append("")
        
        # Main task
        sections.append("## TASK")
        sections.append(task)
        sections.append("")
        
        # Context (if provided)
        if context:
            sections.append("## CONTEXT")
            for key, value in context.items():
                sections.append(f"### {key.replace('_', ' ').title()}")
                sections.append(str(value))
                sections.append("")
        
        # Requirements
        if requirements:
            sections.append("## REQUIREMENTS")
            for i, req in enumerate(requirements, 1):
                # Mark critical requirements
                if any(keyword in req.lower() for keyword in ['must', 'critical', 'important', 'exactly']):
                    sections.append(f"🔴 **CRITICAL {i}**: {req}")
                else:
                    sections.append(f"• {req}")
            sections.append("")
        
        # Examples (if provided)
        if examples:
            sections.append("## EXAMPLES")
            sections.append(examples)
            sections.append("")
        
        # Output format (if provided)
        if output_format:
            sections.append("## OUTPUT FORMAT")
            sections.append("⚠️ **IMPORTANT**: Your response must be in this exact format:")
            sections.append(output_format)
            sections.append("")
        
        return "\n".join(sections)

    def _get_decipher_info(self, step: dict, deciphers_map: dict) -> tuple[str, str, str]:
        """
        Extract decipher information from the step and deciphers_map.
        
        Returns:
            tuple[str, str, str]: (decipher_info, cli_command, decipher_class_name)
        """
        decipher_info = ""
        cli_command = ""
        decipher_class_name = "None"
        
        if "decipher_id" in step:
            decipher = deciphers_map.get(step["decipher_id"])
            if decipher:
                cli_command = decipher['cli_command']
                decipher_class_name = decipher['class_name']
                decipher_info = f"""
                Related Decipher Information:
                - Import: from {decipher['import_path']} import {decipher_class_name}
                - Decipher class name: {decipher_class_name}
                - CLI Command: {cli_command}
                - Expected Output Format: {yaml.dump(decipher.get('json_example', {}), default_flow_style=False)}
                """
        
        return decipher_info, cli_command, decipher_class_name

    def _create_test_step_prompt(self, 
                                zcode_snippets: str,
                                test_file_content: str,
                                previous_steps_description: list[str],
                                step: dict,
                                decipher_info: str) -> str:
        """Create a structured prompt for test step implementation."""
        return self._create_structured_prompt(
            role="Python network automation expert specializing in test automation",
            task="Implement a test step by updating the existing test file content. Add the implementation to the test method following the existing structure.",
            requirements=[
                "MUST follow the existing test structure and patterns",
                "MUST add clear comments explaining the implementation",
                "MUST use the code snippets as reference for implementation patterns",
                "If decipher information is provided:",
                "  • MUST use the import statement to import the decipher class",
                "  • MUST execute command using: cli_session.send_command(command=CLI_COMMAND, decipher=DECIPHER_CLASS_NAME)",
                "  • MUST use the expected output format to validate results",
                "IMPORTANT: Extract step logic into separate method if possible",
                "IMPORTANT: Add logger at beginning of test step with step number",
                "IMPORTANT: Generate complete updated test file content",
                "IMPORTANT: Define constants instead of hardcoded values (e.g., WAIT_TIME_SECONDS = 60)",
                "IMPORTANT: Use meaningful constant names in UPPER_CASE format",
                "IMPORTANT: Place constants at class level or module level as appropriate",
                "CRITICAL: DO NOT include any markdown formatting or code blocks",
                "CRITICAL: DO NOT use backticks (```) or language tags like ```python",
                "CRITICAL: Return only raw Python code without any markdown delimiters"
            ],
            context={
                "code_snippets": zcode_snippets,
                "current_test_file": test_file_content,
                "previous_steps": previous_steps_description,
                "step_details": yaml.dump(step, default_flow_style=False),
                "decipher_info": decipher_info
            },
            output_format="""
# new_file_content
[Complete updated test file content]

# explanation
[Explanation of changes made]
"""
        )

    def _process_test_step_response(self, content: str, messages: list[dict]) -> tuple[Optional[str], Optional[str], bool]:
        """
        Process OpenAI response for test step creation.
        
        Returns:
            tuple[Optional[str], Optional[str], bool]: (new_file_content, explanation, success)
        """
        # Split into new file content and explanation
        parts = content.split("# new_file_content")
        if len(parts) != 2:
            messages.append({
                "role": "user",
                "content": "Your response is missing the '# new_file_content' marker. Please provide the response in the correct format with new file content and explanation sections."
            })
            return None, None, False
        
        file_content_part = parts[1].split("# explanation")
        if len(file_content_part) != 2:
            messages.append({
                "role": "user",
                "content": "Your response is missing the '# explanation' marker. Please provide the response in the correct format with new file content and explanation sections."
            })
            return None, None, False
        
        new_file_content = file_content_part[0].strip()
        explanation = file_content_part[1].strip()
        
        return new_file_content, explanation, True

    def create_test_step(self, 
                        zcode_snippets: str, 
                        deciphers_map: dict, 
                        step: dict, 
                        test_file_path: str, 
                        test_file_content: str,
                        previous_steps_description: list[str]) -> dict:
        """
        Create a test step implementation by updating the test file.
        
        Args:
            zcode_snippets: Code snippets for reference patterns
            deciphers_map: Map of available deciphers
            step: Step definition to implement
            test_file_path: Path to the test file to update
            test_file_content: Current content of the test file
            previous_steps_description: List of previous step descriptions
            
        Returns:
            dict: Updated step with test_file_content and explanation
        """
        # Extract decipher information
        decipher_info, cli_command, decipher_class_name = self._get_decipher_info(step, deciphers_map)
        
        # Create structured prompt
        prompt = self._create_test_step_prompt(
            zcode_snippets, test_file_content, previous_steps_description, step, decipher_info
        )
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": "You are a Python network automation expert specializing in test automation. You must respond with executable Python code that follows the project's structure and standards."},
            {"role": "user", "content": prompt}
        ]

        # Process with retry logic
        for attempt in range(MAX_ATTEMPTS):
            print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
            self._save_messages(messages)
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.1
            )
            print("Received response from OpenAI")
            
            # Check for empty response
            content = response.choices[0].message.content
            if not content:
                messages.append({
                    "role": "user",
                    "content": "OpenAI returned empty response. Please provide the response in the correct format with new file content and explanation sections."
                })
                continue
            
            # Process the response
            new_file_content, explanation, success = self._process_test_step_response(content, messages)
            
            if success and new_file_content and explanation:
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

        # If we reach here, all attempts failed
        print(f"Failed to generate test step after {MAX_ATTEMPTS} attempts")
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
        

         # TEMPORARY
        # deciphers_map_path = os.path.join(test_folder_path, "deciphers_map.pkl")
        # if os.path.exists(deciphers_map_path):
        #     print(f"Loading existing deciphers_map from {deciphers_map_path}")
        #     with open(deciphers_map_path, "rb") as f:
        #         deciphers_map = pickle.load(f)
        # else:
        # TEMPORARY
        deciphers_map = {}
        
        steps_description = []

        for step in steps:
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
                decipher = self.create_decipher(step, test_folder_path)
                deciphers_map[decipher["decipher_id"]] = decipher

            # TEMPORARY
            # Save deciphers_map to a file for later loading/deserialization
            # deciphers_map_path = os.path.join(test_folder_path, "deciphers_map.pkl")
            # with open(deciphers_map_path, "wb") as f:
            #     pickle.dump(deciphers_map, f)
            # TEMPORARY
        
            # Refresh test_file_content with current file content before each step
            with open(test_file_path, "r") as f:
                current_test_file_content = f.read()
            
            res = self.create_test_step(zcode_snippets, 
                deciphers_map, 
                step, 
                test_file_path, 
                current_test_file_content,
                steps_description)

            steps_description.append(res["explanation"])