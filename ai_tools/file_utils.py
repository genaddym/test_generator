import os
import re
import pickle
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """Utilities for file system operations."""
    
    @staticmethod
    def sanitize_folder_name(name: str) -> str:
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
        MAX_FOLDER_NAME_LENGTH = 200
        if len(sanitized) > MAX_FOLDER_NAME_LENGTH:
            sanitized = sanitized[:MAX_FOLDER_NAME_LENGTH].rstrip('_')
        
        return sanitized
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure parent directory exists
            FileUtils.ensure_directory_exists(os.path.dirname(file_path))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    @staticmethod
    def save_pickle(obj: Any, file_path: str) -> None:
        """
        Save an object to a pickle file.
        
        Args:
            obj: Object to save
            file_path: Path to save the pickle file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            FileUtils.ensure_directory_exists(os.path.dirname(file_path))
            
            with open(file_path, "wb") as f:
                pickle.dump(obj, f)
            logger.debug(f"Successfully saved pickle to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save pickle to {file_path}: {e}")
            raise
    
    @staticmethod
    def load_pickle(file_path: str) -> Any:
        """
        Load an object from a pickle file.
        
        Args:
            file_path: Path to the pickle file
            
        Returns:
            Loaded object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        try:
            with open(file_path, "rb") as f:
                obj = pickle.load(f)
            logger.debug(f"Successfully loaded pickle from {file_path}")
            return obj
        except Exception as e:
            logger.error(f"Failed to load pickle from {file_path}: {e}")
            raise
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(file_path)


class ProcessUtils:
    """Utilities for running external processes."""
    
    @staticmethod
    def run_pytest(test_file: str, verbose_flags: Optional[list[str]] = None) -> Tuple[int, str]:
        """
        Run pytest in a subprocess and capture its output.
        
        Args:
            test_file: Path to the test file
            verbose_flags: Pytest verbosity flags
            
        Returns:
            Tuple[int, str]: (exit_code, output)
        """
        if verbose_flags is None:
            verbose_flags = ["-vv"]
        
        # Add the project root to Python path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = project_root

        # Run pytest in a subprocess
        cmd = ["pytest", str(test_file)] + verbose_flags
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Pytest timed out for {test_file}")
            return 1, "Pytest execution timed out"
        except Exception as e:
            logger.error(f"Failed to run pytest for {test_file}: {e}")
            return 1, f"Failed to run pytest: {str(e)}"

    @staticmethod
    def run_pylint(file_path: str, pylint_args: Optional[list[str]] = None) -> Tuple[int, str]:
        """
        Run pylint on a file and capture its output.
        
        Args:
            file_path: Path to the file to check
            pylint_args: Additional pylint arguments
            
        Returns:
            Tuple[int, str]: (exit_code, output)
        """
        if pylint_args is None:
            pylint_args = []
        
        cmd = ["pylint", str(file_path)] + pylint_args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=60  # 1 minute timeout
            )
            return result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Pylint timed out for {file_path}")
            return 1, "Pylint execution timed out"
        except Exception as e:
            logger.error(f"Failed to run pylint for {file_path}: {e}")
            return 1, f"Failed to run pylint: {str(e)}"


class CacheUtils:
    """Utilities for caching operations."""
    
    @staticmethod
    def get_cache_file_path(cache_dir: str, cache_key: str, extension: str = ".pkl") -> str:
        """
        Generate a cache file path.
        
        Args:
            cache_dir: Cache directory
            cache_key: Unique cache key
            extension: File extension
            
        Returns:
            Cache file path
        """
        sanitized_key = FileUtils.sanitize_folder_name(cache_key)
        return os.path.join(cache_dir, f"{sanitized_key}{extension}")
    
    @staticmethod
    def is_cache_valid(cache_file: str, source_file: Optional[str] = None) -> bool:
        """
        Check if cache is valid (exists and optionally newer than source).
        
        Args:
            cache_file: Path to cache file
            source_file: Optional source file to compare modification time
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not FileUtils.file_exists(cache_file):
            return False
        
        if source_file and FileUtils.file_exists(source_file):
            cache_mtime = os.path.getmtime(cache_file)
            source_mtime = os.path.getmtime(source_file)
            return cache_mtime >= source_mtime
        
        return True 