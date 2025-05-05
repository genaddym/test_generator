from abc import ABC, abstractmethod
import re

class Decipher(ABC):
    """
    Abstract base class for CLI output deciphering.
    """

    @abstractmethod
    def decipher(self, raw_output: str) -> dict:
        pass

class ShowRouteForwardingtableIpv4Ipv4PrefixDecipher(Decipher):
    """
    Decipher class to parse 'show route forwarding-table ipv4 IPV4_PREFIX' CLI output.
    Extracts destination, next-hop(s), interface(s), and active/alternate status.
    """

    def decipher(self, raw_output: str) -> dict:
        """
        Parse the CLI output and return a structured dictionary representing the forwarding table.

        Args:
            raw_output (str): Raw CLI output string.

        Returns:
            dict: Parsed forwarding table information.
        """
        result = {}
        lines = raw_output.splitlines()
        forwarding_table = {}
        next_hops = []
        enhanced_alternate = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("Destination:"):
                destination = line.split("Destination:")[1].strip()
                forwarding_table['destination'] = destination
                next_hops = []
                i += 1
                # Parse next-hop and interface lines until next section or end
                while i < len(lines):
                    sub_line = lines[i].strip()
                    if sub_line.startswith("next-hop("):
                        # e.g. next-hop(1): 96.217.0.229 Active
                        m = re.match(r'next-hop\(\d+\):\s+(\S+)(?:\s+(Active))?', sub_line)
                        if m:
                            nh_ip = m.group(1)
                            active = bool(m.group(2) == "Active")
                            next_hops.append({'next-hop': nh_ip, 'active': active})
                    elif sub_line.startswith("interface:"):
                        # e.g. interface: bundle-178
                        iface = sub_line.split("interface:")[1].strip()
                        if next_hops:
                            # Assign interface to last next-hop
                            next_hops[-1]['interface'] = iface
                    elif sub_line.startswith("Enhanced-Alternate:"):
                        # Parse enhanced alternate block
                        enhanced_alternate = {}
                        i += 1
                        while i < len(lines):
                            alt_line = lines[i].strip()
                            if alt_line.startswith("next-hop:"):
                                enhanced_alternate['next-hop'] = alt_line.split("next-hop:")[1].strip()
                            elif alt_line.startswith("interface:"):
                                enhanced_alternate['interface'] = alt_line.split("interface:")[1].strip()
                            else:
                                break
                            i += 1
                        # After parsing enhanced alternate, break to outer loop
                        continue
                    else:
                        # End of forwarding table block
                        break
                    i += 1
                forwarding_table['next-hops'] = next_hops
                if enhanced_alternate:
                    forwarding_table['enhanced-alternate'] = enhanced_alternate
                result['forwarding-table'] = forwarding_table
                # No need to continue parsing after destination block
                break
            i += 1
        return result