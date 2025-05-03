# pragma: exclude file
"""
Module defining constants and utilities for SSH client connections.
This module provides regular expressions for ANSI escape sequence handling,
default prompts, buffer sizes, and key sequence definitions for terminal control.
"""

import re
from enum import Enum

ansi_regex = (
    r"\x1b("
    r"(\[\??\d+[hl])|"
    r"([=<>a-kzNM78])|"
    r"([\(\)][a-b0-2])|"
    r"(\[\d{0,2}[ma-dgkjqi])|"
    r"(\[\d+;\d+[hfy]?)|"
    r"(\[;?[hf])|"
    r"(#[3-68])|"
    r"([01356]n)|"
    r"(O[mlnp-z]?)|"
    r"(/Z)|"
    r"(\d+)|"
    r"(\[\?\d;\d0c)|"
    r"(\d;\dR))"
)

remove_regex = r"\r([ ]+)?"  # NOSONAR  # noqa: B002

ANSI_ESCAPE = re.compile(ansi_regex, flags=re.IGNORECASE)
REMOVE_CHARS = re.compile(remove_regex, flags=re.IGNORECASE)

DEFAULT_DEVICE_PROMPT_REGEX = r"(.*)[$#>] ?$"

MAX_BUFFER = 65535

NO_OUTPUT_EXCEPTION_MSG = "Expected output from command, received none."


class KeySequence(Enum):
    """
    Enumeration of special key sequences for terminal control.

    These constants represent control characters and special keys that can be sent
    to a terminal session to perform various actions like interrupting processes,
    sending tab characters, or handling input.

    Attributes:
        CTRL_C: Control-C character (interrupt signal)
        CTRL_D: Control-D character (end of file)
        CTRL_Z: Control-Z character (suspend process)
        TAB: Tab character for completion
        SPACE: Space character
        BACKSPACE: Backspace character for deleting input
    """

    CTRL_C = "\x03"
    CTRL_D = "\x04"
    CTRL_Z = "\x1a"
    TAB = "\x09"
    SPACE = "\x20"
    BACKSPACE = "\x08"
