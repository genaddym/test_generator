"""
Data objects for interface mappings.
This module contains data classes that represents
the mapping of interface long names to their short names and descriptions.
"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class InterfaceMapping:
    """
    An InterfaceMapping represents the mapping of interface
    long names to their short names and descriptions.
    """

    full_name: str
    description: str
    short_name: str
