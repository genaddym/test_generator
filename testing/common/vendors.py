# pragma: exclude file
"""
Module defining vendor enumerations for network equipment manufacturers.
This module provides standardized vendor identifiers used throughout the testing framework.
"""

from enum import Enum


class Vendors(Enum):
    """
    Enumeration of supported network equipment vendors.

    These vendor identifiers are used for vendor-specific implementations,
    validation logic, and device classification throughout the testing framework.

    Attributes:
        DRIVENETS: DriveNets network
        CISCO: Cisco network
        ARISTA: Arista network
    """

    DRIVENETS = "drivenets"
    CISCO = "cisco"
    ARISTA = "arista"
