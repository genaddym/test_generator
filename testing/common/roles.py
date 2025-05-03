# pragma: exclude file
"""
Module defining role enumerations for network roles.
This module provides standardized role identifiers used throughout the testing framework.
"""

from enum import Enum


class Roles(Enum):
    """
    Enumeration of supported network roles.
    """

    ASBR = "asbr"
    TCR = "tcr"
    PCR = "pcr"
    SCR = "scr"
    MPE = "mpe"
    CCR = "ccr"
    OTHER = "other"
