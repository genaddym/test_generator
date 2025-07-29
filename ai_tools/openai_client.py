import os
import json
import re
import logging
from typing import Optional, Tuple, List, Dict, Any

import yaml

from .config import OpenAIClientConfig
from .gateway import OpenAIChatGateway
from .models import StepInfo, DecipherInfo, TestGenerationResult, PromptAnalysisResult
from .prompt_builders import (
    CLICommandExtractionPromptBuilder,
    DecipherGenerationPromptBuilder, 
    TestStepPromptBuilder,
    PromptAnalysisPromptBuilder,
    PylintFixPromptBuilder
)
from .file_utils import FileUtils, ProcessUtils, CacheUtils

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Refactored OpenAI client with structured components and proper error handling."""
    
    def __init__(self, config: Optional[OpenAIClientConfig] = None):
        """
        Initialize the OpenAI client with configuration.
        
        Args:
            config: OpenAI client configuration. If not provided, loads from environment.
        """
        self.config = config or OpenAIClientConfig.from_environment()
        self.config.validate()
        
        self.gateway = OpenAIChatGateway(self.config)
        
        logger.info(f"Initialized OpenAI client with model: {self.config.model}")

    def _save_messages(self, messages: List[Dict[str, str]], file_name: str = "last_prompt.txt"):
        """Save messages to file for debugging."""
        try:
            with open(file_name, "w") as f:
                for message in messages:
                    f.write(f"{message['role']}: {message['content']}\n")
        except Exception as e:
            logger.warning(f"Failed to save messages to {file_name}: {e}")

    def analyze_test_prompt(self, prompt_content: Dict[str, Any]) -> PromptAnalysisResult:
        """
        Analyze the test prompt quality and determine if it's sufficient for test generation.
        
        Args:
            prompt_content: The YAML content of the prompt file
            
        Returns:
            PromptAnalysisResult with analysis details
        """
        try:
            prompt, messages = PromptAnalysisPromptBuilder.build_prompt_and_messages(prompt_content)
            
            logger.info("Analyzing test prompt quality...")
            # Convert typed messages to dict for _save_messages
            dict_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            self._save_messages(dict_messages)
            
            content = self.gateway.create_chat_completion_with_content(messages)
            analysis = json.loads(content)
            
            quality_score = float(analysis["quality_score"])
            issues = analysis["issues"]
            can_proceed = quality_score >= self.config.prompt_quality_threshold
            
            logger.info(f"Prompt Quality Analysis:")
            logger.info(f"Quality Score: {quality_score}/10")
            logger.info(f"Can Proceed: {can_proceed}")
            if issues:
                logger.info("Identified Issues:")
                for i, issue in enumerate(issues, 1):
                    logger.info(f"{i}. {issue}")
            logger.info(f"Analysis: {analysis['explanation']}")
            
            return PromptAnalysisResult(
                can_proceed=can_proceed,
                quality_score=quality_score,
                issues=issues,
                explanation=analysis['explanation']
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return PromptAnalysisResult(
                can_proceed=False, 
                quality_score=0.0, 
                issues=["Failed to analyze prompt quality"]
            )

    def create_decipher(self, step_data: Dict[str, Any], test_folder_path: str) -> DecipherInfo:
        """
        Create a decipher for a test step.
        
        Args:
            step_data: Step dictionary data
            test_folder_path: Path to the test folder
            
        Returns:
            DecipherInfo object with decipher details
        """
        step = StepInfo.from_dict(step_data)
        
        # Extract CLI command
        prompt, messages = CLICommandExtractionPromptBuilder.build_prompt_and_messages(step)
        
        logger.info("Extracting CLI command...")
        dict_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        self._save_messages(dict_messages)
        
        cli_command = self.gateway.create_chat_completion_with_content(messages).strip()
        logger.info(f"Extracted CLI command: {cli_command}")
        
        # Create folder and paths
        folder_name = FileUtils.sanitize_folder_name(cli_command)
        command_folder = os.path.join(test_folder_path, folder_name)
        FileUtils.ensure_directory_exists(command_folder)
        
        # Generate class name
        class_name = ''.join(word.capitalize() for word in folder_name.split('_'))
        
        # Check cache
        decipher_id = step_data.get("decipher_id", "unknown_decipher")
        cache_file = CacheUtils.get_cache_file_path(command_folder, decipher_id)
        
        if CacheUtils.is_cache_valid(cache_file):
            logger.info(f"Loading cached decipher from {cache_file}")
            try:
                cached_data = FileUtils.load_pickle(cache_file)
                return DecipherInfo(
                    id=cached_data["decipher_id"],
                    cli_command=cached_data["cli_command"],
                    class_name=cached_data["class_name"],
                    import_path=cached_data["import_path"],
                    json_example=cached_data.get("json_example"),
                    folder_path=command_folder
                )
            except Exception as e:
                logger.warning(f"Failed to load cached decipher: {e}")
        
        # Generate decipher and unit test
        decipher_info = self._generate_decipher_implementation(
            step, cli_command, class_name, command_folder
        )
        
        # Cache the result
        try:
            FileUtils.save_pickle(decipher_info.to_dict(), cache_file)
            logger.info(f"Cached decipher to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache decipher: {e}")
        
        return decipher_info

    def _generate_decipher_implementation(
        self, 
        step: StepInfo, 
        cli_command: str, 
        class_name: str, 
        command_folder: str
    ) -> DecipherInfo:
        """Generate decipher implementation with retry logic."""
        
        # Create import path
        relative_path = os.path.relpath(command_folder, os.path.dirname(command_folder))
        import_path = relative_path.replace(os.path.sep, '.')
        
        decipher_file = os.path.join(command_folder, "decipher.py")
        unit_test_file = os.path.join(command_folder, "unit_test.py")
        
        for attempt in range(self.config.max_attempts):
            try:
                if not (FileUtils.file_exists(decipher_file) and FileUtils.file_exists(unit_test_file)):
                    # Generate new files
                    prompt, messages = DecipherGenerationPromptBuilder.build_prompt_and_messages(
                        step, cli_command, class_name
                    )
                    
                    logger.info(f"Generating decipher implementation (attempt {attempt + 1})")
                    dict_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                    self._save_messages(dict_messages)
                    
                    content = self.gateway.create_chat_completion_with_content(messages)
                    self._parse_and_save_decipher_response(content, decipher_file, unit_test_file)
                
                # Test the implementation
                exit_code, test_output = ProcessUtils.run_pytest(
                    unit_test_file, self.config.pytest_verbose_flags
                )
                
                if exit_code == 0:
                    logger.info(f"Test {unit_test_file} PASSED")
                    
                    # Extract JSON example
                    json_example = self._extract_json_example(unit_test_file)
                    
                    return DecipherInfo(
                        id=step.decipher_id or "unknown",
                        cli_command=cli_command,
                        class_name=f"{class_name}Decipher",
                        import_path=f"{import_path}.decipher",
                        json_example=json_example,
                        folder_path=command_folder
                    )
                else:
                    logger.warning(f"Test failed (attempt {attempt + 1}): {test_output}")
                    if attempt < self.config.max_attempts - 1:
                        # Add error feedback for next attempt
                        continue
                    
            except Exception as e:
                logger.error(f"Error in decipher generation (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_attempts - 1:
                    raise
        
        raise RuntimeError(f"Failed to generate working decipher after {self.config.max_attempts} attempts")

    def _parse_and_save_decipher_response(self, content: str, decipher_file: str, unit_test_file: str):
        """Parse OpenAI response and save decipher files."""
        parts = content.split("# decipher.py")
        if len(parts) != 2:
            raise ValueError("Response missing '# decipher.py' marker")
        
        decipher_part = parts[1].split("# unit_test.py")
        if len(decipher_part) != 2:
            raise ValueError("Response missing '# unit_test.py' marker")
        
        unit_test_part = decipher_part[1].split("# explanation")
        if len(unit_test_part) != 2:
            raise ValueError("Response missing '# explanation' marker")
        
        decipher_code = decipher_part[0].strip()
        unit_test_code = unit_test_part[0].strip()
        explanation = unit_test_part[1].strip()
        
        logger.info("Implementation Explanation:")
        logger.info("=" * 80)
        logger.info(explanation)
        logger.info("=" * 80)
        
        FileUtils.write_file(decipher_file, decipher_code)
        FileUtils.write_file(unit_test_file, unit_test_code)

    def _extract_json_example(self, unit_test_file: str) -> Optional[Dict[str, Any]]:
        """Extract JSON example from unit test file."""
        try:
            test_content = FileUtils.read_file(unit_test_file)
            json_match = re.search(r'expected_output\s*=\s*({[^{}]*(?:{[^{}]*}[^{}]*)*})', test_content)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception as e:
            logger.warning(f"Could not extract JSON example: {e}")
        return None

    def create_test_file(self, test_name: str, test_folder_path: str) -> Tuple[str, str]:
        """
        Create a new test file from template with proper class and method names.
        
        Args:
            test_name: Name of the test
            test_folder_path: Path to the test folder
            
        Returns:
            Tuple of (test_file_path, test_file_content)
        """
        test_file = os.path.join(test_folder_path, f"{test_name}.py")
        
        if FileUtils.file_exists(test_file):
            content = FileUtils.read_file(test_file)
        else:
            # Read template and customize
            template_content = FileUtils.read_file(self.config.test_template_file)
            
            # Convert test_name to camel case for class name
            class_name = ''.join(word.capitalize() for word in test_name.split('_'))
            
            # Replace class and method names
            content = template_content.replace("class TestTemplate", f"class Test{class_name}")
            content = content.replace("def test_template", f"def {test_name}")
            
            FileUtils.write_file(test_file, content)
        
        return test_file, content

    def create_test_step(
        self,
        code_snippets: str,
        deciphers_map: Dict[str, DecipherInfo],
        step_data: Dict[str, Any],
        test_file_path: str,
        test_file_content: str,
        previous_steps_description: List[str]
    ) -> StepInfo:
        """
        Create a test step implementation.
        
        Args:
            code_snippets: Reference code snippets
            deciphers_map: Available deciphers
            step_data: Step data
            test_file_path: Path to test file
            test_file_content: Current test file content
            previous_steps_description: Previous step descriptions
            
        Returns:
            Updated StepInfo
        """
        step = StepInfo.from_dict(step_data)
        
        # Get decipher info
        decipher_info = ""
        if step.decipher_id and step.decipher_id in deciphers_map:
            decipher = deciphers_map[step.decipher_id]
            decipher_info = f"""
            Related Decipher Information:
            - Import: from {decipher.import_path} import {decipher.class_name}
            - Decipher class name: {decipher.class_name}
            - CLI Command: {decipher.cli_command}
            - Expected Output Format: {yaml.dump(decipher.json_example or {}, default_flow_style=False)}
            """
        
        # Generate test step implementation
        for attempt in range(self.config.max_attempts):
            try:
                prompt, messages = TestStepPromptBuilder.build_prompt_and_messages(
                    code_snippets, test_file_content, previous_steps_description, step, decipher_info
                )
                
                logger.info(f"Generating test step (attempt {attempt + 1})")
                dict_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                self._save_messages(dict_messages)
                
                content = self.gateway.create_chat_completion_with_content(messages)
                
                # Parse response
                new_file_content, explanation = self._parse_test_step_response(content)
                
                if new_file_content and explanation:
                    logger.info("Implementation Explanation:")
                    logger.info("=" * 80)
                    logger.info(explanation)
                    logger.info("=" * 80)
                    
                    FileUtils.write_file(test_file_path, new_file_content)
                    
                    step.test_file_content = new_file_content
                    step.explanation = explanation
                    return step
                
            except Exception as e:
                logger.error(f"Error generating test step (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_attempts - 1:
                    raise
        
        raise RuntimeError(f"Failed to generate test step after {self.config.max_attempts} attempts")

    def _parse_test_step_response(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse test step response."""
        parts = content.split("# new_file_content")
        if len(parts) != 2:
            return None, None
        
        file_content_part = parts[1].split("# explanation")
        if len(file_content_part) != 2:
            return None, None
        
        return file_content_part[0].strip(), file_content_part[1].strip()

    def fix_pylint_issues(self, file_path: str) -> bool:
        """
        Fix pylint issues in a file.
        
        Args:
            file_path: Path to the file to fix
            
        Returns:
            True if issues were fixed successfully, False otherwise
        """
        for attempt in range(self.config.max_attempts):
            exit_code, pylint_output = ProcessUtils.run_pylint(file_path, self.config.pylint_args)
            
            if exit_code == 0:
                logger.info("Pylint validation passed!")
                return True
            
            logger.warning(f"Pylint found issues (attempt {attempt + 1}):")
            logger.warning(pylint_output)
            
            if attempt < self.config.max_attempts - 1:
                try:
                    current_content = FileUtils.read_file(file_path)
                    
                    prompt, messages = PylintFixPromptBuilder.build_prompt_and_messages(
                        file_path, pylint_output, current_content
                    )
                    
                    logger.info("Requesting pylint fixes...")
                    dict_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                    self._save_messages(dict_messages)
                    
                    content = self.gateway.create_chat_completion_with_content(messages)
                    fixed_content = self._parse_pylint_fix_response(content)
                    
                    if fixed_content:
                        FileUtils.write_file(file_path, fixed_content)
                    else:
                        logger.warning("Failed to parse pylint fix response")
                        break
                        
                except Exception as e:
                    logger.error(f"Error fixing pylint issues: {e}")
                    break
        
        logger.warning(f"Could not fix all pylint issues after {self.config.max_attempts} attempts")
        return False

    def _parse_pylint_fix_response(self, content: str) -> Optional[str]:
        """Parse pylint fix response."""
        parts = content.split("# fixed_code")
        if len(parts) != 2:
            return None
        
        code_part = parts[1].split("# explanation")
        if len(code_part) != 2:
            return None
        
        explanation = code_part[1].strip()
        logger.info("Code Fix Explanation:")
        logger.info("=" * 80)
        logger.info(explanation)
        logger.info("=" * 80)
        
        return code_part[0].strip()

    def generate_test(self, test_name: str) -> TestGenerationResult:
        """
        Generate a complete test with all steps.
        
        Args:
            test_name: Name of the test to generate
            
        Returns:
            TestGenerationResult with generation details
        """
        test_folder_path = os.path.join("tests", "lab1", test_name)
        
        try:
            # Load code snippets
            code_snippets = FileUtils.read_file(self.config.code_snippets_file)
            
            # Load test prompt
            guide_file = os.path.join(test_folder_path, "prompt.yml")
            with open(guide_file, "r") as f:
                steps_data = yaml.safe_load(f)
            
            # Analyze prompt quality
            analysis = self.analyze_test_prompt(steps_data)
            # if not analysis.can_proceed:
            #     logger.warning("Test generation halted due to insufficient prompt quality")
            #     return TestGenerationResult(
            #         test_name=test_name,
            #         test_file_path="",
            #         quality_score=analysis.quality_score,
            #         quality_issues=analysis.issues,
            #         success=False,
            #         error_message="Insufficient prompt quality"
            #     )
            
            # Create test file
            test_file_path, test_file_content = self.create_test_file(test_name, test_folder_path)
            
            # Generate deciphers and test steps
            deciphers_map = {}
            steps = []
            steps_description = []
            
            for step_data in steps_data:
                logger.info(f"Processing step: {step_data}")
                
                step = StepInfo.from_dict(step_data)
                
                # Create decipher if needed
                if step.has_cli_output:
                    step_key = list(step_data.keys())[0]
                    step.description_key = step_key
                    step.decipher_id = f"{step_key.replace(' ', '_')}_decipher"
                    
                    decipher = self.create_decipher(step.to_dict(), test_folder_path)
                    deciphers_map[step.decipher_id] = decipher
                
                # Update test file content
                current_content = FileUtils.read_file(test_file_path)
                
                # Generate test step
                updated_step = self.create_test_step(
                    code_snippets, deciphers_map, step.to_dict(),
                    test_file_path, current_content, steps_description
                )
                
                steps.append(updated_step)
                steps_description.append(updated_step.explanation or "")
            
            # Fix pylint issues
            pylint_passed = self.fix_pylint_issues(test_file_path)
            
            return TestGenerationResult(
                test_name=test_name,
                test_file_path=test_file_path,
                deciphers=deciphers_map,
                steps=steps,
                quality_score=analysis.quality_score,
                quality_issues=analysis.issues,
                pylint_passed=pylint_passed,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating test: {e}")
            return TestGenerationResult(
                test_name=test_name,
                test_file_path="",
                success=False,
                error_message=str(e)
            ) 