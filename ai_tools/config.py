from dataclasses import dataclass
from typing import Optional
import os

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    
    def load_dotenv():
        """Dummy function when dotenv is not available."""
        pass


@dataclass
class OpenAIClientConfig:
    """Configuration for OpenAI client operations."""
    
    # API Configuration
    api_key: Optional[str] = None
    model: str = "gpt-4.1"
    temperature: float = 0.1
    
    # Retry Configuration
    max_attempts: int = 7
    
    # Quality Thresholds
    prompt_quality_threshold: float = 1.0
    
    # File Configuration
    cache_dir: str = ".cache"
    test_template_file: str = "test_template.py"
    code_snippets_file: str = "code_snippets.py"
    
    # Subprocess Configuration
    pytest_verbose_flags: list[str] = None
    pylint_args: list[str] = None
    
    def __post_init__(self):
        """Initialize default values and load environment variables."""
        if HAS_DOTENV:
            load_dotenv()
        
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if self.pytest_verbose_flags is None:
            self.pytest_verbose_flags = ["-vv"]
            
        if self.pylint_args is None:
            self.pylint_args = []
    
    @classmethod
    def from_environment(cls) -> "OpenAIClientConfig":
        """Create configuration from environment variables with defaults."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            max_attempts=int(os.getenv("MAX_ATTEMPTS", "7")),
            prompt_quality_threshold=float(os.getenv("PROMPT_QUALITY_THRESHOLD", "7.0"))
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it or set OPENAI_API_KEY environment variable")
        
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
            
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
            
        if not 0.0 <= self.prompt_quality_threshold <= 10.0:
            raise ValueError("prompt_quality_threshold must be between 0.0 and 10.0") 