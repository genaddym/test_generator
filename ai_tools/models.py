from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List


@dataclass
class DecipherInfo:
    """Information about a CLI command decipher."""
    
    id: str
    cli_command: str
    class_name: str
    import_path: str
    json_example: Optional[Dict[str, Any]] = None
    folder_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "decipher_id": self.id,
            "cli_command": self.cli_command,
            "class_name": self.class_name,
            "import_path": self.import_path,
            "json_example": self.json_example,
        }


@dataclass
class StepInfo:
    """Information about a test step."""
    
    raw_data: Dict[str, Any]
    description_key: Optional[str] = None
    decipher_id: Optional[str] = None
    cli_command: Optional[str] = None
    class_name: Optional[str] = None
    import_path: Optional[str] = None
    json_example: Optional[Dict[str, Any]] = None
    test_file_content: Optional[str] = None
    explanation: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepInfo":
        """Create StepInfo from dictionary data."""
        return cls(
            raw_data=data,
            description_key=data.get("description_key"),
            decipher_id=data.get("decipher_id"),
            cli_command=data.get("cli_command"),
            class_name=data.get("class_name"),
            import_path=data.get("import_path"),
            json_example=data.get("json_example"),
            test_file_content=data.get("test_file_content"),
            explanation=data.get("explanation"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        result = self.raw_data.copy()
        if self.description_key is not None:
            result["description_key"] = self.description_key
        if self.decipher_id is not None:
            result["decipher_id"] = self.decipher_id
        if self.cli_command is not None:
            result["cli_command"] = self.cli_command
        if self.class_name is not None:
            result["class_name"] = self.class_name
        if self.import_path is not None:
            result["import_path"] = self.import_path
        if self.json_example is not None:
            result["json_example"] = self.json_example
        if self.test_file_content is not None:
            result["test_file_content"] = self.test_file_content
        if self.explanation is not None:
            result["explanation"] = self.explanation
        return result
    
    @property
    def has_cli_output(self) -> bool:
        """Check if step has CLI output example."""
        return "cli_output_example" in self.raw_data
    
    @property
    def command_id(self) -> str:
        """Get command ID for this step."""
        return self.raw_data.get("command_id", "unknown_command")
    
    @property
    def cli_output_example(self) -> Optional[str]:
        """Get CLI output example."""
        return self.raw_data.get("cli_output_example")


@dataclass
class TestGenerationResult:
    """Result of test generation process."""
    
    test_name: str
    test_file_path: str
    deciphers: Dict[str, DecipherInfo] = field(default_factory=dict)
    steps: List[StepInfo] = field(default_factory=list)
    quality_score: float = 0.0
    quality_issues: List[str] = field(default_factory=list)
    pylint_passed: bool = False
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class PromptAnalysisResult:
    """Result of prompt quality analysis."""
    
    can_proceed: bool
    quality_score: float
    issues: List[str]
    explanation: str = "" 