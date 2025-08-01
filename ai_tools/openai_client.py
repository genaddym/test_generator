import os
from typing import Optional, Tuple
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import re
import json
import subprocess
import pickle
import ast
import copy

OPENAI_MODEL = "gpt-4.1"
# "gpt-4.1"


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
        self.debug_mode = False  # Default to non-debug mode
    
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
        # Also remove brackets, parentheses, hyphens, and other problematic characters
        illegal_chars = r'[<>:"|?*\\/#\[\](){}@!$%^&+=;,\'`~-]'
        
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

    def _create_messages(self, system_content: str, user_content: str) -> list[dict]:
        """Create properly typed messages for OpenAI chat completion."""
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    def create_decipher(self, step: dict, test_folder_path: str) -> dict:
        prompt = self._create_structured_prompt(
            role="Python network automation expert specializing in CLI command parsing and testing",
            task="""Extract the CLI command from the provided step details.
Understand which parts of the extracted command represent dynamic or variable parameters according to the test needs
For each identified dynamic value, replace its specific instance in the command with a descriptive, uppercase with underscores parameter name.
If the "Step Details" hint at the purpose of the parameter, incorporate that into the name (e.g., SOURCE_IP_ADDRESS, DESTINATION_PORT).
""",
            requirements=[
                "MUST return only the CLI command text",
                "MUST NOT include any explanations or additional text",
                "MUST extract the exact command that needs to be executed",
                "MUST for each identified dynamic value, replace its specific instance in the command with a descriptive, uppercase parameter name."
            ],
            context={
                "step_details": step[step["description_key"]],
                "clarifications": yaml.dump(step.get('clarifications', {}), default_flow_style=False)
            }
        )

        messages = self._create_messages(
            "You are a Python network automation expert specializing in CLI command parsing and testing.",
            prompt
        )

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
        # decipher_pickle_file = os.path.join(command_folder, f"{decipher_id}.pkl")
        
        # # Check if cached decipher exists in the command folder
        # if os.path.exists(decipher_pickle_file):
        #     print(f"Loading cached decipher from {decipher_pickle_file}")
        #     try:
        #         with open(decipher_pickle_file, "rb") as f:
        #             cached_step = pickle.load(f)
        #         print(f"Successfully loaded cached decipher: {cached_step.get('class_name', 'Unknown')}")
        #         return cached_step
        #     except Exception as e:
        #         print(f"Failed to load cached decipher from {decipher_pickle_file}: {e}")
        #         print("Proceeding with fresh decipher generation...")

        class_name = ''.join(word.capitalize() for word in folder_name.split('_'))
        step["class_name"] = f"{class_name}Decipher"
        
        # Create import path
        relative_path = os.path.relpath(command_folder, os.path.dirname(command_folder))
        import_path = relative_path.replace(os.path.sep, '.')
        step["import_path"] = f"{import_path}.decipher"

        # Generate initial implementation using structured prompt
        prompt = self._create_structured_prompt(
            role="Python network automation expert specializing in CLI command parsing and testing",
            task=f"""Deciphers (parsers) are responsible for converting string text from CLI responses into Python dictionaries. Generate a decipher class named '{class_name}Decipher' and corresponding unit test to parse CLI command output and extract relevant data for test automation.\n\n{step[step['description_key']]}
            Assume that the provided CLI output examples are the full expected output from the command.
            Pay attention to the clarifications that might be provided below.
            """,
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
                "cli_output_example": step.get('cli_output_example', ''),
                "clarifications": yaml.dump(step.get('clarifications', {}), default_flow_style=False)
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

                    # TEMPORARY: Replace the import statement in the decipher file
                    with open(decipher_file, 'r') as f:
                        decipher_content = f.read()
                    
                    decipher_content = decipher_content.replace(
                        "from tests.base.decipher import Decipher",
                        "from orbital.testing.helpers.deciphers.decipher_base import Decipher"
                    )
                    
                    with open(decipher_file, 'w') as f:
                        f.write(decipher_content)
                    # TEMPORARY

                    # Extract expected_output using ast to safely parse Python assignments
                    try:
                        # Parse the entire file
                        tree = ast.parse(test_content)
                        
                        # Look for assignment to expected_output
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name) and target.id == 'expected_output':
                                        # Get the value being assigned
                                        if isinstance(node.value, ast.Str):
                                            # If it's a string literal, parse it as JSON
                                            json_str = node.value.s
                                        elif isinstance(node.value, ast.Dict):
                                            # If it's a dictionary literal, convert to string
                                            json_str = ast.literal_eval(node.value)
                                        else:
                                            continue
                                        
                                        try:
                                            if isinstance(json_str, dict):
                                                json_example = json_str
                                            else:
                                                json_example = json.loads(json_str)
                                            step["json_example"] = json_example
                                            break
                                        except json.JSONDecodeError as e:
                                            print(f"Warning: Could not parse JSON from expected_output in {unit_test_file}: {str(e)}")
                                            print(f"Content: {json_str}")
                                            
                    except SyntaxError as e:
                        print(f"Warning: Could not parse Python file {unit_test_file}: {str(e)}")
                    except Exception as e:
                        print(f"Warning: Error processing expected_output from {unit_test_file}: {str(e)}")
                    
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
        
        if hasattr(self, 'debug_mode') and self.debug_mode:
            input("Prompt saved. Press Enter to continue after reviewing the saved messages...")

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
        context = {
            "code_snippets": zcode_snippets,
            "current_test_file": test_file_content,
            "previous_steps": previous_steps_description,
            "step_details": yaml.dump(step, default_flow_style=False),
            "decipher_info": decipher_info
        }
        
        # Add clarifications if available
        if 'clarifications' in step:
            context["clarifications"] = yaml.dump(step['clarifications'], default_flow_style=False)
            
        return self._create_structured_prompt(
            role="Python network automation expert specializing in test automation",
            task="""Implement a test step by updating the existing test file content. Add the implementation to the test method following the existing structure.
            Pay attention to the clarifications that might be provided below.
            If the step contains CLI command, use the decipher class to parse the output. Use the decipher output example from the provided decipher map, to understand the expected output format.
            """,
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
                "CRITICAL: DO NOT remove any unused imports, constants, variables, or methods - they will be used in later steps"
                "To effectively inform users about the validation process, add INFO level logs that are both informative and concise."
            ],
            context=context,
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
                        previous_steps_description: list[str],
                        test_folder_path: str) -> tuple[dict, dict]:
        """
        Create a test step implementation by updating the test file.
        
        Args:
            zcode_snippets: Code snippets for reference patterns
            deciphers_map: Map of available deciphers
            step: Step definition to implement
            test_file_path: Path to the test file to update
            test_file_content: Current content of the test file
            previous_steps_description: List of previous step descriptions
            test_folder_path: Path to the test folder for decipher creation
            
        Returns:
            tuple[dict, dict]: (Updated step with test_file_content and explanation, updated deciphers_map)
        """
                # Print step description for clarity
        print("\nProcessing test step:")
        print("=" * 80)
        print(yaml.dump(step, default_flow_style=False))
        print("=" * 80)


        # Handle decipher creation if needed
        if "cli_output_example" in step:
            step_key = list(step.keys())[0]  # Get the first key (e.g., "step 1")
            step["description_key"] = step_key
            decipher_id = f"{step_key.replace(' ', '_')}_decipher"
            step["decipher_id"] = decipher_id
            decipher = self.create_decipher(step, test_folder_path)
            deciphers_map[decipher["decipher_id"]] = decipher



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
                return step, deciphers_map

        # If we reach here, all attempts failed
        print(f"Failed to generate test step after {MAX_ATTEMPTS} attempts")
        return step, deciphers_map

    def analyze_test_prompt(self, prompt_content: dict, test_folder_path: str) -> tuple[bool, dict]:
        """
        Analyze the test prompt quality and gather necessary clarifications from the user.
        
        Args:
            prompt_content (dict): The YAML content of the prompt file
            test_folder_path (str): Path to the test folder where the prompt is located

        Returns:
            tuple[bool, dict]: (can_proceed, enriched_prompt)
            - can_proceed: Whether the prompt quality is sufficient to proceed
            - enriched_prompt: Original prompt with added clarifications
        """
        QUALITY_THRESHOLD = 5.0  # Minimum score to proceed with test generation
        
        prompt = self._create_structured_prompt(
            role="Test prompt quality analyst",
            task="""Analyze the test prompt and identify areas needing clarification for automated test generation.
Analyze if the provided test description is clear enough for automated code generation. The test step can contain CLI command. Cli command should be specified. In case and the step contains cli command, it must contains the example of the cli output for that command.
In case and the step contains cli command, further step generation logic will create a decipher for it.
Deciphers (parsers) are responsible for converting string text from CLI responses into structured Python objects. Each decipher implements a specific parsing logic
for a particular type of CLI output.
Assume that the provided CLI output examples are the full expected output from the command
Understand which parts of the extracted command represent dynamic or variable parameters according to the test needs. If that information is missing, ask for user clarification.
It should be clear from the test prompt, what information should be extracted by decipher, according to the test needs.""",
            requirements=[
                "MUST rate prompt quality on scale 0-10 (10 being perfect)",
                "MUST analyze each step for clarity",
                "MUST generate specific clarification questions for unclear aspects",
                "MUST provide suggested answer options for each question",
                "MUST check if steps are logically ordered",
                "MUST check for missing dependencies between steps"
            ],
            context={
                "prompt_content": yaml.dump(prompt_content, default_flow_style=False)
            },
            output_format="""
            {
                "quality_score": <float 0-10>,
                "can_proceed": <boolean>,
                "step_questions": {
                    "<step_key>": [
                        {
                            "question": "<question text>",
                            "suggested_answers": [
                                "<option 1>",
                                "<option 2>",
                                ...
                            ],
                            "explanation": "<why this needs clarification>"
                        },
                        ...
                    ],
                    ...
                },
                "general_issues": [
                    "<issue_1>",
                    "<issue_2>",
                    ...
                ],
                "explanation": "<detailed analysis>"
            }
            """
        )

        messages = [
            {"role": "system", "content": "You are a test prompt quality analyst. You must evaluate test prompts for clarity and identify areas needing clarification."},
            {"role": "user", "content": prompt}
        ]

        print("\nAnalyzing test prompt quality...")
        self._save_messages(messages)
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.1
        )

        try:
            content = response.choices[0].message.content
            if not content:
                print("Error: Received empty response from OpenAI")
                return False, prompt_content
                
            analysis = json.loads(content)
            quality_score = float(analysis["quality_score"])
            step_questions = analysis["step_questions"]
            general_issues = analysis["general_issues"]
            
            print(f"\nPrompt Quality Analysis:")
            print("=" * 80)
            print(f"Quality Score: {quality_score}/10")
            print(f"Can Proceed: {quality_score >= QUALITY_THRESHOLD}")

            if general_issues:
                print("\nGeneral Issues:")
                for i, issue in enumerate(general_issues, 1):
                    print(f"{i}. {issue}")

            print(f"\nAnalysis: {analysis['explanation']}")
            print("=" * 80)
            
            # If quality is too low, don't proceed with clarifications
            if quality_score < QUALITY_THRESHOLD:
                print("\nTest generation halted due to insufficient prompt quality.")
                print("Please address the general issues and try again.")
                return False, prompt_content

            # Process clarification questions for each step
            enriched_prompt = prompt_content.copy()
            if step_questions:
                print("\nSome aspects of the test steps need clarification.")
                print("Please provide clarification by either:")
                print("1. Entering the number of a suggested answer")
                print("2. Providing your own clarification text\n")

                for step_key, questions in step_questions.items():
                    if not questions:  # Skip steps without questions
                        continue

                    print(f"\nClarifications needed for {step_key}:")
                    clarifications = {}

                    for i, q in enumerate(questions, 1):
                        while True:
                            print(f"\nQuestion {i}: {q['question']}")
                            print("Suggested answers:")
                            for j, ans in enumerate(q['suggested_answers'], 1):
                                print(f"  {j}. {ans}")
                            user_input = input("\nYour clarification (enter answer number or free text): ").strip()

                            # Try to interpret as answer number
                            try:
                                ans_num = int(user_input)
                                if 1 <= ans_num <= len(q['suggested_answers']):
                                    clarifications[q['question']] = q['suggested_answers'][ans_num - 1]
                                    break
                            except ValueError:
                                # User provided free text
                                clarifications[q['question']] = user_input
                                break

                            print("Invalid input. Please try again.")

                    # Find the step in the prompt content and add clarifications
                    for step in enriched_prompt:
                        if step_key in step:
                            step['clarifications'] = clarifications
                            break

                # Save enriched prompt to a file in the test folder
                enriched_prompt_file = os.path.join(test_folder_path, "enriched_prompt.yml")
                with open(enriched_prompt_file, "w") as f:
                    yaml.dump(enriched_prompt, f, default_flow_style=False)
                print(f"\nEnriched prompt saved to {enriched_prompt_file}")

            return True, enriched_prompt
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing analysis response: {str(e)}")
            return False, prompt_content

    def run_pylint(self, file_path: str) -> Tuple[int, str]:
        """
        Run pylint on a file and capture its output.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            Tuple[int, str]: (exit_code, output)
        """
        # Run pylint in a subprocess
        result = subprocess.run(
            ["pylint", str(file_path)],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        return result.returncode, result.stdout + result.stderr

    def fix_pylint_issues(self, file_path: str, pylint_output: str, current_content: str) -> str:
        """
        Use OpenAI to fix pylint issues in the file.
        
        Args:
            file_path (str): Path to the file being fixed
            pylint_output (str): Output from pylint containing issues
            current_content (str): Current content of the file
            
        Returns:
            str: Fixed file content
        """
        prompt = self._create_structured_prompt(
            role="Python code quality expert",
            task="Fix pylint issues in the provided Python code while maintaining its functionality.",
            requirements=[
                "MUST fix all pylint issues reported",
                "MUST maintain exact functionality",
                "MUST keep all imports and dependencies",
                "MUST follow PEP 8 style guide",
                "MUST return complete fixed file content",
                "MUST NOT include any markdown formatting",
                "MUST NOT use backticks or code blocks"
            ],
            context={
                "current_code": current_content,
                "pylint_issues": pylint_output,
                "file_path": file_path
            },
            output_format="""
            # fixed_code
            [Complete fixed file content]

            # explanation
            [Explanation of fixes made]
            """
        )

        messages = [
            {"role": "system", "content": "You are a Python code quality expert. You must fix pylint issues while maintaining code functionality."},
            {"role": "user", "content": prompt}
        ]

        print("\nRequesting OpenAI to fix pylint issues...")
        self._save_messages(messages)
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.1
        )

        content = response.choices[0].message.content
        if not content:
            return current_content

        # Extract fixed code
        parts = content.split("# fixed_code")
        if len(parts) != 2:
            return current_content

        code_part = parts[1].split("# explanation")
        if len(code_part) != 2:
            return current_content

        fixed_code = code_part[0].strip()
        explanation = code_part[1].strip()

        print("\nCode Fix Explanation:")
        print("=" * 80)
        print(explanation)
        print("=" * 80)

        return fixed_code

    def fix_prompt_file_format(self, file_content: str) -> list[dict]:
        """
        Fixes a ill formed YAML fole by means of OpenAI API
        Args:
            file_content (str): The content of the YAML file
        Returns:
            list[dict]: Parsed YAML steps as Python objects
        """
        exmple_prompt = Path(__file__).parent / "resources/example_prompt_format.yml"
        example_prompt_content = ""
        if exmple_prompt.exists():
            with open(exmple_prompt, "r") as f:
                example_prompt_content = f.read()
        if not example_prompt_content:
            raise RuntimeError("Example prompt format file not found or empty. Expected path : " + exmple_prompt.as_posix())

        prompt = self._create_structured_prompt(
            role="You are an AI Agent that know to perform text-to-yaml conversion",
            task="Apply a set of rules to a given free text file to structure it into yaml. the yaml will represent a structured description of some networking test",
            requirements=[
                """Step Identification Patterns: Look for lines starting with "- step" followed by a number and colon. Examples include "- step 1:", "- step: 3", "- step1:". Accept variations in formatting but step numbers should be sequential, though handle gaps gracefully.""",
                """Step Description Extraction: The step description starts immediately after the step identifier. It may be on the same line as the step identifier or on subsequent indented lines. Description can be a single quoted string like "Execute on DUT: show command", a multi-line block starting with pipe symbol for literal block scalar, or plain text that continues until CLI output or next step is found.""",
                """Substeps: If a step is subdivided into substeps, each substep should be treated as a separate step with its own "step <number>" key. For example, if step 1 has substeps, they should be numbered as "step 1.1", "step 1.2", etc. IMPORTANT: If there is only a single substep for a particular step, DO NOT create a substep in the generated YAML. All the substep information should remain within the main step block in the generated YAML.""",
                """CLI Output Detection: Look for indicators such as "cli output", "here is the cli output", "example cli output". CLI output typically follows keywords like "here is the cli output", "example cli output", "CLI command output:". CLI output continues until next step marker or end of file.""",
                """YAML Structure Requirements: Generate a YAML list where each item represents one step. Each step item contains 1-2 keys maximum: "step <number>" which is required and contains the step description, and "cli_output_example" which is optional and contains raw CLI command output.""",
                """Step Key Formatting: Always use format "step <number>" such as "step 1", "step 2". Preserve original step numbering from input text. Use space between "step" and the number.""",
                """Description Value Formatting: If description is single line and simple, use quoted string format. If description is multi-line or contains special characters, use literal block scalar with pipe symbol. Preserve original quotes if they exist in the description. Remove any leading or trailing whitespace from descriptions.""",
                """CLI Output Formatting: Always use literal block scalar with pipe symbol for "cli_output_example" values. Preserve exact formatting, spacing, and special characters from CLI output. Include empty lines and table formatting as-is. Do not add quotes around CLI output content.""",
                """Content Extraction Logic: For step description, extract text between step identifier and CLI output indicator or next step. For CLI output, extract text after CLI output indicator until next step marker or end of file. Handle indentation properly by removing common leading whitespace but preserve relative indentation. Skip empty lines at the beginning and end of extracted content.""",
                """Special Content Handling: Preserve table formatting in both descriptions and CLI output. Maintain code snippets and command syntax with backticks. Keep technical terms and device names exactly as written. Preserve numbered and bulleted lists within descriptions.""",
                """Error Handling Rules: If step number is missing or malformed, assign sequential numbers. If CLI output is mentioned but not found, omit "cli_output_example" key. If step description is empty, use placeholder "Step description not provided". Handle incomplete or malformed input gracefully.""",
                """Validation Requirements: Ensure each step has valid YAML syntax. Verify step numbers are unique and properly formatted. Confirm CLI output, if present, maintains original formatting. Check that no content from input text is lost or corrupted.""",
                """Output Formatting Standards: Use 2-space indentation for YAML. Place "cli_output_example" immediately after corresponding step description. Maintain consistent spacing between list items. End file with single newline character.""",
                """Don't truncate or modify cli_output_example and preserve the exact formatting, spacing, and special characters from CLI output. Include empty lines and/or new lines and table formatting as-is. Do not add quotes around CLI output content.""",
            ],
            context={
                "example_prompt_content": example_prompt_content,
                "prompt_content": file_content,
            },
            output_format="""
            <the generated yaml file>
            """
        )

        messages = [
            {"role": "system", "content": "You need to transform the etxt file into yaml structure following the specifued rules"},
            {"role": "user", "content": prompt}
        ]

        print("\nAsking OpenAI to fix the YAML format...")
        self._save_messages(messages)
        content = ""
        for attempt in range(MAX_ATTEMPTS):
            print(f"Sending prompt to OpenAI... Attempt {attempt + 1} of {MAX_ATTEMPTS}")
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            print("Received response from OpenAI:\n<response>\n%s\n</response>" % content)
            if not content:
                print("Error: Received empty response from OpenAI")
                messages.append({
                    "role": "user",
                    "content": "OpenAI returned empty response. Please provide the response in the correct format with new file content and explanation sections."
                })
                continue
            try:
                steps = yaml.safe_load(content)
                if not isinstance(steps, list):
                    print("Error: OpenAI response is not a valid YAML list")
                    messages.append({
                        "role": "user",
                        "content": f"Your response is not a valid YAML list. It has type {type(steps)}. Please fix it and return a valid YAML list."
                    })
                    continue
                if len(steps) == 0:
                    print("Error: OpenAI response is an empty YAML list")
                    messages.append({
                        "role": "user",
                        "content": "Your response is an empty YAML list. Please fix it and return a valid YAML list with at least one step."
                    })
                    continue
                return steps
            except yaml.YAMLError as e:
                print(f"Error parsing YAML content: {str(e)}")
                messages.append({
                    "role": "user",
                    "content": f"Your response is not valid YAML. Please fix it and return valid YAML content.\n\n{content}. got yaml.YAMLError {str(e)} while trying to perform yaml.safe_load(content) on it. Please fix the YAML format and try again."
                })
                continue
        raise RuntimeError("OpenAI failed to convert the prompt to YAML format after all attempts. Please check the prompt and try again.")

    def save_ai_generated_prompt(self,
                                 existing_prompt_file: str,
                                 new_prompt_content: list[dict],):
        """
        Save the AI-generated prompt content to a file.
        The file will have the suffix '_ai_generated' added to the original file name.
        If this name already exists,  a new file with the suffix '_ai_generated.1' or "_ai_generated.2| etc will be created.
        """
        class LiteralStr(str):
            pass

        def literal_str_representer(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

        def wrap_cli_output_example(data: list | dict):
            """
            Recursively wrap cli_output_example values in LiteralStr for block style YAML.
            """
            if isinstance(data, list):
                for item in data:
                    wrap_cli_output_example(item)
            elif isinstance(data, dict):
                for k, v in data.items():
                    if k == "cli_output_example" and isinstance(v, str):
                        data[k] = LiteralStr(v)
                    else:
                        wrap_cli_output_example(v)

        # needed to properly print \n chars in cli output in generated yaml file
        yaml.add_representer(LiteralStr, literal_str_representer)

        existing = Path(existing_prompt_file)
        # extract the file anem,up to teh suffix
        file_name = existing.stem
        file_suffix = existing.suffix
        # create the new file name
        new_file_name = f"{file_name}_ai_generated.yml"
        new_file_path = existing.parent / new_file_name
        # Check if the file already exists
        if new_file_path.exists():
            print(
                f"File {new_file_path.as_posix()} already exists."
                "Please confirm if you want to overwrite it. (Yes/No): default=Yes"
            )
            answer= input().strip().lower() or "yes"
            if answer.lower() not in ["yes", "y"]:
                print("Exiting without saving the AI-generated prompt.")
                return
        # Write the new prompt content to the file
        copied = copy.deepcopy(new_prompt_content)
        wrap_cli_output_example(copied)
        with open(new_file_path, "w") as f:
            yaml.dump(
                copied,
                f,
                default_flow_style=False,
                default_style=None,
                sort_keys=False,
            )
        print(f"AI-generated prompt saved to {new_file_path.as_posix()}")

    def get_test_prompt(self, test_name: str) -> str:
        """
        Identifies the `prompt.txt` plain text file corresponding to the test_name and returns its content.
        """
        test_folder_path = os.path.join("tests", "lab1", test_name)
        if not os.path.exists(test_folder_path):
            raise FileNotFoundError(f"Test folder not found: {test_folder_path}")

        guide_file = os.path.join(test_folder_path, "prompt.txt")
        if not os.path.exists(guide_file):
            raise FileNotFoundError(f"Prompt file not found: {guide_file}")

        return guide_file

    def convert_prompt(self, test_name: str) -> list[dict]:
        """
        Retrieve the steps from the prompt YAML file.

        Args:
            test_name (str): Name of the test

        Returns:
            list[dict]: List of steps defined in the prompt
        """
        prompt_file = self.get_test_prompt(test_name)

        yaml_prompt_content = None
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        file_content = ""
        with open(prompt_file, "r") as f:
            file_content = f.read()

        try:
            yaml_prompt_content = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {prompt_file}: {str(e)}")
            print("Asking OpenAI to fix the YAML format...")
            yaml_prompt_content = self.fix_prompt_file_format(file_content)

        self.save_ai_generated_prompt(prompt_file, yaml_prompt_content)

        return yaml_prompt_content

    def generate_test(self, test_name: str):
        # Ask user about debug mode
        debug_mode = input("Run test generation in debug mode? (y/n): ").lower().strip() == 'y'
        self.debug_mode = debug_mode
        
        test_folder_path = os.path.join("tests", "lab1", test_name)

        with open("code_snippets.py", "r") as f:
            zcode_snippets = f.read()

        guide_file = os.path.join(test_folder_path, "prompt.yml")
        with open(guide_file, "r") as f:
            steps = yaml.safe_load(f)
            
        # Analyze prompt quality and gather clarifications before proceeding
        can_proceed, enriched_steps = self.analyze_test_prompt(steps, test_folder_path)
        if not can_proceed:
            return

        # Create test file from template
        test_file_path, test_file_content = self.create_test_file(test_name, test_folder_path)
        
        deciphers_map = {}
        steps_description = []

        for step in enriched_steps:
            print(f"\nProcessing step: {step}")
        
            # Refresh test_file_content with current file content before each step
            with open(test_file_path, "r") as f:
                current_test_file_content = f.read()
            
            res, deciphers_map = self.create_test_step(zcode_snippets, 
                deciphers_map, 
                step, 
                test_file_path, 
                current_test_file_content,
                steps_description,
                test_folder_path)

            steps_description.append(res["explanation"])

        # Run pylint validation and fix issues
        print("\nValidating test file with pylint...")
        attempt = 0
        while attempt < MAX_ATTEMPTS:
            exit_code, pylint_output = self.run_pylint(test_file_path)
            
            if exit_code == 0:
                print("Pylint validation passed!")
                break
                
            print(f"\nPylint found issues (attempt {attempt + 1} of {MAX_ATTEMPTS}):")
            print(pylint_output)
            
            # Read current content
            with open(test_file_path, "r") as f:
                current_content = f.read()
            
            # Try to fix issues
            fixed_content = self.fix_pylint_issues(test_file_path, pylint_output, current_content)
            
            # Write fixed content
            with open(test_file_path, "w") as f:
                f.write(fixed_content)
            
            attempt += 1
            
        if attempt == MAX_ATTEMPTS:
            print("\nWarning: Could not fix all pylint issues after maximum attempts.")

        