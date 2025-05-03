# pragma: exclude file
"""
Arista Interface Mappings
"""

from orbital.testing.common.vendor_utils.interface_mappings.data_objects import (
    InterfaceMapping,
)

# List of Arista Interface Mappings
arista_interface_mappings: list[InterfaceMapping] = [
    InterfaceMapping("Ethernet", "Standard Ethernet interfaces", "Et"),
    InterfaceMapping("Management", "Out-of-band management interface", "Mgmt"),
    InterfaceMapping("Loopback", "Loopback interface", "Lo"),
    InterfaceMapping(
        "Port-Channel", "Aggregated link of multiple Ethernet interfaces", "Po"
    ),
    InterfaceMapping(
        "Tunnel", "Virtual interface for tunneling protocols", "Tu"
    ),
]
