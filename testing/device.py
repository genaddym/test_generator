# pragma: exclude file
"""
This module defines the Device class used for representing network devices.
"""

from dataclasses import dataclass


@dataclass
class Device:
    """
    A class to represent a network device.

    Attributes:
        hostname: The hostname of the device
        username: The username for accessing the device
        password: The password for accessing the device
        vendor: The vendor of the device
        port: The port number for accessing the device (optional)
    """

    hostname: str
    username: str
    password: str
    vendor: str
    port: int | None = None

    def __str__(self) -> str:
        return str(self.__dict__)
