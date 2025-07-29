from typing import Optional, Dict, Any, List
from openai.types.chat import ChatCompletionMessageParam
import yaml
import textwrap

from .models import StepInfo, DecipherInfo


class PromptBuilder:
    """Base class for building structured prompts."""
    
    @staticmethod
    def create_messages(system_content: str, user_content: str) -> List[ChatCompletionMessageParam]:
        """Create properly typed messages for OpenAI chat completion."""
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    
    @staticmethod
    def create_structured_prompt(
        role: str,
        task: str, 
        requirements: List[str],
        context: Optional[Dict[str, Any]] = None,
        examples: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> str:
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


class CLICommandExtractionPromptBuilder(PromptBuilder):
    """Builder for CLI command extraction prompts."""
    
    @classmethod
    def build_prompt_and_messages(cls, step: StepInfo) -> tuple[str, List[ChatCompletionMessageParam]]:
        """Build prompt and messages for CLI command extraction."""
        prompt = cls.create_structured_prompt(
            role="Python network automation expert specializing in CLI command parsing and testing",
            task="Extract the CLI command from the provided step details.",
            requirements=[
                "MUST return only the CLI command text",
                "MUST NOT include any explanations or additional text",
                "MUST extract the exact command that needs to be executed"
            ],
            context={
                "step_details": step.raw_data[step.description_key] if step.description_key else str(step.raw_data)
            }
        )

        messages = cls.create_messages(
            "You are a Python network automation expert specializing in CLI command parsing and testing.",
            prompt
        )
        
        return prompt, messages


class DecipherGenerationPromptBuilder(PromptBuilder):
    """Builder for decipher generation prompts."""
    
    @classmethod
    def build_prompt_and_messages(cls, step: StepInfo, cli_command: str, class_name: str) -> tuple[str, List[ChatCompletionMessageParam]]:
        """Build prompt and messages for decipher generation."""
        prompt = cls.create_structured_prompt(
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
                "step_details": yaml.dump(step.to_dict(), default_flow_style=False),
                "class_name": class_name
            },
            output_format=textwrap.dedent("""
                # decipher.py
                [Python code for decipher.py]

                # unit_test.py
                [Python code for unit_test.py]

                # explanation
                [Short summary of implementation and design decisions]
            """).strip()
        )
        
        messages = [
            {"role": "system", "content": "You are a Python network automation expert specializing in CLI command parsing and testing. You must respond with executable Python code and explanations in the specified format."},
            {"role": "user", "content": prompt}
        ]
        
        return prompt, messages


class TestStepPromptBuilder(PromptBuilder):
    """Builder for test step implementation prompts."""
    
    @classmethod
    def build_prompt_and_messages(
        cls,
        code_snippets: str,
        test_file_content: str,
        previous_steps_description: List[str],
        step: StepInfo,
        decipher_info: str
    ) -> tuple[str, List[ChatCompletionMessageParam]]:
        """Build prompt and messages for test step implementation."""
        prompt = cls.create_structured_prompt(
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
                "code_snippets": code_snippets,
                "current_test_file": test_file_content,
                "previous_steps": previous_steps_description,
                "step_details": yaml.dump(step.to_dict(), default_flow_style=False),
                "decipher_info": decipher_info
            },
            output_format=textwrap.dedent("""
                # new_file_content
                [Complete updated test file content]

                # explanation
                [Explanation of changes made]
            """).strip()
        )
        
        messages = [
            {"role": "system", "content": "You are a Python network automation expert specializing in test automation. You must respond with executable Python code that follows the project's structure and standards."},
            {"role": "user", "content": prompt}
        ]
        
        return prompt, messages


class PromptAnalysisPromptBuilder(PromptBuilder):
    """Builder for prompt quality analysis."""
    
    @classmethod
    def build_prompt_and_messages(cls, prompt_content: Dict[str, Any]) -> tuple[str, List[ChatCompletionMessageParam]]:
        """Build prompt and messages for prompt quality analysis."""
        prompt = cls.create_structured_prompt(
            role="Test prompt quality analyst",
            task="Analyze the provided test prompt and evaluate its quality for automated test generation.",
            requirements=[
                "MUST rate prompt quality on scale 0-10 (10 being perfect)",
                "MUST identify any unclear or ambiguous parts",
                "MUST check if steps are logically ordered",
                "MUST verify each step has clear success criteria",
                "MUST check if required test data/configuration is specified",
                "MUST validate CLI command examples are complete and correct",
                "MUST ensure expected outputs are clearly defined",
                "MUST check for missing dependencies between steps"
            ],
            context={
                "prompt_content": yaml.dump(prompt_content, default_flow_style=False)
            },
            output_format=textwrap.dedent("""
                {
                    "quality_score": <float 0-10>,
                    "can_proceed": <boolean>,
                    "issues": [
                        "<issue_1>",
                        "<issue_2>",
                        ...
                    ],
                    "explanation": "<detailed analysis>"
                }
            """).strip()
        )

        messages = [
            {"role": "system", "content": "You are a test prompt quality analyst. You must evaluate test prompts for clarity, completeness, and feasibility for automated test generation."},
            {"role": "user", "content": prompt}
        ]
        
        return prompt, messages


class PylintFixPromptBuilder(PromptBuilder):
    """Builder for pylint issue fixing prompts."""
    
    @classmethod
    def build_prompt_and_messages(cls, file_path: str, pylint_output: str, current_content: str) -> tuple[str, List[ChatCompletionMessageParam]]:
        """Build prompt and messages for fixing pylint issues."""
        prompt = cls.create_structured_prompt(
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
            output_format=textwrap.dedent("""
                # fixed_code
                [Complete fixed file content]

                # explanation
                [Explanation of fixes made]
            """).strip()
        )

        messages = [
            {"role": "system", "content": "You are a Python code quality expert. You must fix pylint issues while maintaining code functionality."},
            {"role": "user", "content": prompt}
        ]
        
        return prompt, messages 