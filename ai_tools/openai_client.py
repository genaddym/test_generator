import os
from typing import Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import json

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

        Based on the provided project context, test template, and test documentation, generate a detailed implementation guide for creating the test components, divided into steps. The guide should include:

        1. Understand what CLI commands are required to implement the test.
        2. Required Deciphers. Create a new step for each CLI command and decipher that is required to implement for this CLI command:
           - Specify the CLI command that is being parsed.
           - Provide an example of the full CLI command output. Find the corresponding output in the command outputs file.
           - Specify the required data objects for parsed output.
           - For each CLI command, a folder with the command name should be created. 
           Into this folder, a file called `decipher.py`, file called `data_object.py` and a file called `unit_test.py` should be created.
           - Each decipher should inherit from DecipherBase, implement the `decipher` method and return a data object.
           - A unit test should be created in the `unit_test.py` file.
           - Instruct to use the command outputs to create the unit test.



        Format the output as a markdown document with clear sections and subsections.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a network testing expert that helps create test implementations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        
        # Save the implementation guide to a file
        implementation_guide = response.choices[0].message.content
        guide_file = os.path.join(test_folder_path, "implementation_guide.md")
        
        with open(guide_file, "w") as f:
            f.write(implementation_guide)
    
    def generate_test(self, test_folder_path: str) -> str:
        """
        Generate test implementation and return the implementation guide content.
        
        Args:
            test_folder_path (str): Path to the test folder containing documentation files
            
        Returns:
            str: Generated implementation instructions
        """
        # Create the implementation guide file
        self.create_implementation_guide(test_folder_path)
        
        # Read and return the generated guide
        guide_file = os.path.join(test_folder_path, "implementation_guide.md")
        with open(guide_file, "r") as f:
            return f.read() 