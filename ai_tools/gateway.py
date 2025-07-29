import time
import logging
from typing import List, Optional
from functools import wraps
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion

from .config import OpenAIClientConfig

logger = logging.getLogger(__name__)


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator


class OpenAIChatGateway:
    """Gateway for OpenAI chat completions with retry logic and proper typing."""
    
    def __init__(self, config: OpenAIClientConfig):
        """Initialize the gateway with configuration."""
        config.validate()
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
    
    @with_retry()
    def create_chat_completion(
        self, 
        messages: List[ChatCompletionMessageParam],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> ChatCompletion:
        """
        Create a chat completion with retry logic.
        
        Args:
            messages: List of properly typed chat messages
            temperature: Override default temperature
            model: Override default model
            
        Returns:
            ChatCompletion response from OpenAI
        """
        return self.client.chat.completions.create(
            model=model or self.config.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.config.temperature
        )
    
    def get_content_from_response(self, response: ChatCompletion) -> str:
        """
        Extract content from chat completion response.
        
        Args:
            response: ChatCompletion response
            
        Returns:
            Content string from the response
            
        Raises:
            ValueError: If response contains no content
        """
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty response")
        return content
    
    def create_chat_completion_with_content(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Create chat completion and return content directly.
        
        Args:
            messages: List of properly typed chat messages
            temperature: Override default temperature
            model: Override default model
            
        Returns:
            Content string from the response
        """
        response = self.create_chat_completion(messages, temperature, model)
        return self.get_content_from_response(response) 