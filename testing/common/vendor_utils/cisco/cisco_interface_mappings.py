# pragma: exclude file
"""
Cisco Interface Mappings
"""

from orbital.testing.common.vendor_utils.interface_mappings.data_objects import (
    InterfaceMapping,
)

# List of Cisco Interface Mappings
cisco_interface_mappings: list[InterfaceMapping] = [
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
