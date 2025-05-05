from abc import ABC, abstractmethod
import re

class Decipher(ABC):
    """
    Abstract base class for CLI output deciphering.
    """

    @abstractmethod
    def decipher(self, raw_output: str) -> dict:
        pass

class ShowRouteForwardingtableIpv6Ipv6PrefixDecipher(Decipher):
    """
    Decipher class to parse 'show route forwarding-table ipv6 IPV6_PREFIX' CLI output.
    Extracts destination, next-hop(s), interface(s), and active/alternate status.
    """

    def decipher(self, raw_output: str) -> dict:
        """
        Parse the raw CLI output and return a structured dictionary representing
        the forwarding table for the specified IPv6 prefix.

        Args:
            raw_output (str): Raw CLI output string.

        Returns:
            dict: Parsed forwarding table information.
        """
        result = {}
        lines = raw_output.splitlines()
        destination = None
        forwarding_table = {}
        current_section = None

        # Regex patterns
        dest_pattern = re.compile(r"^Destination:\s+(\S+)")
        nexthop_pattern = re.compile(r"^\s*next-hop(?:\((\d+)\))?:\s+(\S+)(?:\s+(Active))?")
        interface_pattern = re.compile(r"^\s*interface:\s+(\S+)")
        enhanced_alt_pattern = re.compile(r"^\s*Enhanced-Alternate:")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            dest_match = dest_pattern.match(line)
            if dest_match:
                destination = dest_match.group(1)
                forwarding_table = {
                    "destination": destination,
                    "next_hops": [],
                    "enhanced_alternate": []
                }
                i += 1
                continue

            if enhanced_alt_pattern.match(line):
                current_section = "enhanced_alternate"
                i += 1
                continue

            if current_section == "enhanced_alternate":
                nh_match = nexthop_pattern.match(line)
                if nh_match:
                    nh_ip = nh_match.group(2)
                    # Check if next line is interface
                    interface = None
                    if i + 1 < len(lines):
                        intf_match = interface_pattern.match(lines[i+1].strip())
                        if intf_match:
                            interface = intf_match.group(1)
                            i += 1
                    forwarding_table["enhanced_alternate"].append({
                        "next_hop": nh_ip,
                        "interface": interface
                    })
                    i += 1
                    continue
                else:
                    current_section = None
                    i += 1
                    continue

            nh_match = nexthop_pattern.match(line)
            if nh_match:
                nh_ip = nh_match.group(2)
                nh_active = bool(nh_match.group(3) == "Active")
                interface = None
                if i + 1 < len(lines):
                    intf_match = interface_pattern.match(lines[i+1].strip())
                    if intf_match:
                        interface = intf_match.group(1)
                        i += 1
                forwarding_table["next_hops"].append({
                    "next_hop": nh_ip,
                    "interface": interface,
                    "active": nh_active
                })
                i += 1
                continue

            i += 1

        if destination:
            result = forwarding_table
        return result