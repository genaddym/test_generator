# pragma: exclude file
"""
Base class for deciphers that parse CLI output into structured data objects.

Deciphers are responsible for converting string text from CLI responses into
structured Python objects. Each decipher implements a specific parsing logic
for a particular type of CLI output.
"""

from abc import ABC, abstractmethod


class Decipher(ABC):
    """
    Abstract base class for all deciphers.

    A decipher is responsible for parsing CLI output text and converting it
    into structured data objects. Each subclass must implement the decipher
    method to define its specific parsing logic.
    """

    @staticmethod
    @abstractmethod
    def decipher(cli_response: str) -> object:
        """
        Parse CLI response text into a structured data object.

        Args:
            cli_response: The CLI output text to parse

        Returns:
            A structured data object representing the parsed information
        """
