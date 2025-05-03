"""
Interface mappings are used to match between full interface names and short interface names
"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class InterfaceMapping:
    """
    Represents a mapping between full and short interface names.

    This class stores the relationship between a full interface name (e.g., "GigabitEthernet"),
    its description, and its short name (e.g., "Gi") used in various Cisco CLI outputs.

    Attributes:
        full_name: The complete interface name
        description: Human-readable description of the interface type
        short_name: Abbreviated interface name used in CLI outputs
    """

    full_name: str
    description: str
    short_name: str


# List of Cisco Interface Mappings
interface_mappings: list[InterfaceMapping] = [
    InterfaceMapping("Bundle-Ether", "Aggregated Ethernet interface(s)", "BE"),
    InterfaceMapping("Bundle-POS", "Aggregated POS interface(s)", "BP"),
    InterfaceMapping("CEM", "Circuit Emulation interface(s)", "CEM"),
    InterfaceMapping(
        "FastEthernet", "FastEthernet/IEEE 802.3 interface(s)", "Fa"
    ),
    InterfaceMapping(
        "FiftyGigE", "FiftyGigabitEthernet/IEEE 802.3 interface(s)", "Fi"
    ),
    InterfaceMapping(
        "FortyGigE", "FortyGigabitEthernet/IEEE 802.3 interface(s)", "Fo"
    ),
    InterfaceMapping(
        "FourHundredGigE",
        "FourHundredGigabitEthernet/IEEE 802.3 interface(s)",
        "F",
    ),
    InterfaceMapping(
        "GigabitEthernet", "GigabitEthernet/IEEE 802.3 interface(s)", "Gi"
    ),
    InterfaceMapping(
        "HundredGigE", "HundredGigabitEthernet/IEEE 802.3 interface(s)", "Hu"
    ),
    InterfaceMapping("Loopback", "Loopback interface(s)", "Lo"),
    InterfaceMapping("MgmtEth", "Ethernet/IEEE 802.3 interface(s)", "Mg"),
    InterfaceMapping("Multilink", "Multilink network interface(s)", "Ml"),
    InterfaceMapping("Null", "Null interface", "Nu"),
    InterfaceMapping(
        "POS", "Packet over SONET/SDH network interface(s)", "POS"
    ),
    InterfaceMapping("PW-Ether", "PWHE Ethernet Interface", "PE"),
    InterfaceMapping("PW-IW", "PWHE VC11 IP Interworking Interface", "PI"),
    InterfaceMapping("SRP", "SRP interface(s)", "SRP"),
    InterfaceMapping("Serial", "Serial network interface(s)", "Se"),
    InterfaceMapping(
        "TenGigE", "TenGigabitEthernet/IEEE 802.3 interface(s)", "Te"
    ),
    InterfaceMapping(
        "TwentyFiveGigE",
        "TwentyFiveGigabitEthernet/IEEE 802.3 interface(s)",
        "Tw",
    ),
    InterfaceMapping(
        "TwoHundredGigE",
        "TwoHundredGigabitEthernet/IEEE 802.3 interface(s)",
        "TH",
    ),
    InterfaceMapping("tunnel-ipsec", "IPSec Tunnel interface(s)", "tsec"),
    InterfaceMapping(
        "tunnel-mte", "MPLS Traffic Engineering P2MP Tunnel interface(s)", "tm"
    ),
    InterfaceMapping(
        "tunnel-te", "MPLS Traffic Engineering Tunnel interface(s)", "tt"
    ),
    InterfaceMapping(
        "tunnel-tp", "MPLS Transport Protocol Tunnel interface", "tp"
    ),
]


class InterfaceMappingConverter:
    """
    Utility class for converting between full and short interface names.

        This class provides methods to convert between the full interface names
        (e.g., "GigabitEthernet0/0/0") and short interface names (e.g., "Gi0/0/0")
        used in Cisco devices.

        The class maintains internal mappings between full and short names based on
        the predefined interface_mappings list.
    """

    _short_to_full_mapping: dict[str, str] = {
        interface_mapping.short_name: interface_mapping.full_name
        for interface_mapping in interface_mappings
    }

    _full_to_short_mapping: dict[str, str] = {
        interface_mapping.full_name: interface_mapping.short_name
        for interface_mapping in interface_mappings
    }

    @staticmethod
    def get_full_interface_name(if_name: str) -> str | None:
        """
        Convert a short interface name to its full name.

                If the provided name is already in full format, it will be returned unchanged.

                :param if_name: Interface name to convert (e.g., "Gi0/0/0")
                :type if_name: str
                :return: Full interface name (e.g., "GigabitEthernet0/0/0") or None if not found
                :rtype: str | None
        """
        # check first if the if_name is already in full format
        if InterfaceMappingConverter._contains(
            InterfaceMappingConverter._full_to_short_mapping, if_name
        ):
            return if_name
        return InterfaceMappingConverter._get_interface_name(
            InterfaceMappingConverter._short_to_full_mapping, if_name
        )

    @staticmethod
    def get_short_interface_name(if_name: str) -> str | None:
        """
        Convert a full interface name to its short name.

                If the provided name is already in short format, it will be returned unchanged.

                :param if_name: Interface name to convert (e.g., "GigabitEthernet0/0/0")
                :type if_name: str
                :return: Short interface name (e.g., "Gi0/0/0") or the original name if not found
                :rtype: str | None
        """
        short_name: str | None = InterfaceMappingConverter._get_interface_name(
            InterfaceMappingConverter._full_to_short_mapping, if_name
        )
        # if we provide if_name in short notation, it won't be foun in the mapping
        # _full_to_short_mapping
        return short_name or if_name

    @staticmethod
    def _get_interface_name(
        mappings: dict[str, str], if_name: str
    ) -> str | None:
        """Get mapped interface name from a mapping dictionary.

        :param mappings: Dictionary mapping between interface name formats
        :type mappings: dict[str, str]
        :param if_name: Interface name to look up
        :type if_name: str
        :return: Mapped interface name or None if not found
        :rtype: str | None
        """
        for key, value in mappings.items():
            if not if_name.startswith(key):
                continue
            _, suf = if_name.split(key)
            return value + suf

    @staticmethod
    def _contains(mappings: dict[str, str], if_name: str) -> bool:
        """Check if an interface name starts with any key in the mappings.

        :param mappings: Dictionary mapping between interface name formats
        :type mappings: dict[str, str]
        :param if_name: Interface name to check
        :type if_name: str
        :return: True if interface name starts with any mapping key, False otherwise
        :rtype: bool
        """
        for m in mappings:
            if if_name.startswith(m):
                return True
        return False
