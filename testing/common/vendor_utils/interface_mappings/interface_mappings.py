"""
Interface mappings are used to match between full interface names and short interface names
"""

import re

from orbital.testing.common.vendors import Vendors
from orbital.testing.common.vendor_utils.cisco.cisco_interface_mappings import (
    cisco_interface_mappings,
)
from orbital.testing.common.vendor_utils.arista.arista_interface_mappings import (
    arista_interface_mappings,
)

from .data_objects import InterfaceMapping

__all__ = ["InterfaceMappingConverterFactory", "InterfaceMappingConverter"]


class InterfaceMappingConverterFactory:
    """
    Factory class to create and manage instances of InterfaceMappingConverter
    for different vendors.
    """

    @staticmethod
    def get_converter(vendor: Vendors) -> "InterfaceMappingConverter":
        """
        Retrieves an instance of InterfaceMappingConverter for the specified vendor.

        :param vendor: The vendor enum value specifying which vendor's interface mappings to use
        :type vendor: Vendors
        :return: An instance of InterfaceMappingConverter configured for the specified vendor
        :rtype: InterfaceMappingConverter
        :raises ValueError: If the vendor is not supported
        """
        cls = InterfaceMappingConverterFactory
        if vendor == Vendors.CISCO:
            interface_mappings = cisco_interface_mappings
        elif vendor == Vendors.ARISTA:
            interface_mappings = arista_interface_mappings
        else:
            raise ValueError(f"Unsupported vendor: {vendor}")

        if not hasattr(cls, "vendor_instances"):
            cls.vendor_instances: dict[Vendors, list[InterfaceMapping]] = {}

        if vendor not in cls.vendor_instances:
            cls.vendor_instances[vendor] = InterfaceMappingConverter(
                interface_mappings
            )

        return cls.vendor_instances[vendor]


class InterfaceMappingConverter:
    """
    Converts between full and short interface names for a specific vendor.
    """

    def __init__(self, interface_mappings: list[InterfaceMapping]):
        """
        Initialize the converter with interface mappings.

        :param interface_mappings: List of interface mappings defining the conversion rules
        :type interface_mappings: list[InterfaceMapping]
        """
        self._short_to_full_mapping: dict[str, str] = {
            interface_mapping.short_name: interface_mapping.full_name
            for interface_mapping in interface_mappings
        }

        self._full_to_short_mapping: dict[str, str] = {
            interface_mapping.full_name: interface_mapping.short_name
            for interface_mapping in interface_mappings
        }

    def get_full_interface_name(self, if_name: str) -> str | None:
        """
        Converts an interface name to full name.
        If it is already given in full format, it will be returned unchanged.

        :param if_name: The interface name to convert to full format
        :type if_name: str
        :return: The full interface name or None if conversion fails
        :rtype: str | None
        """
        # check first if the if_name is already in full format
        if self._contains(self._full_to_short_mapping, if_name):
            return if_name
        return self._get_interface_name(self._short_to_full_mapping, if_name)

    def get_short_interface_name(self, if_name: str) -> str | None:
        """
        Converts an interface name to short name.
        If it is already given in short format, it will be returned unchanged.

        :param if_name: The interface name to convert to short format
        :type if_name: str
        :return: The short interface name or the original name if already in short format
        :rtype: str | None
        """
        short_name: str | None = self._get_interface_name(
            self._full_to_short_mapping, if_name
        )
        # if we provide if_name in short notation,
        # it won't be found in the mapping _full_to_short_mapping
        return short_name or if_name

    def _get_interface_name(
        self, mappings: dict[str, str], if_name: str
    ) -> str | None:
        """
        Helper method to get interface name using provided mappings.

        :param mappings: Dictionary containing interface name mappings
        :type mappings: dict[str, str]
        :param if_name: The interface name to look up
        :type if_name: str
        :return: The mapped interface name or None if no mapping found
        :rtype: str | None
        """
        IF_PATTERN = re.compile(r"(?P<name>[A-Za-z\-]+)(?P<number>\d+.*)")
        for key, value in mappings.items():
            if not if_name.startswith(key):
                continue
            match = IF_PATTERN.match(if_name)
            return value + match.group("number")

    def _contains(self, mappings: dict[str, str], if_name: str) -> bool:
        """
        Check if an interface name starts with any of the mapping keys.

        :param mappings: Dictionary containing interface name mappings
        :type mappings: dict[str, str]
        :param if_name: The interface name to check
        :type if_name: str
        :return: True if interface name starts with any mapping key, False otherwise
        :rtype: bool
        """
        for m in mappings:
            if if_name.startswith(m):
                return True
        return False
