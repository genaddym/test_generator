import unittest
from decipher import ShowRouteForwardingtableIpv6Ipv6PrefixDecipher

class TestShowRouteForwardingtableIpv6Ipv6PrefixDecipher(unittest.TestCase):
    """
    Unit test for ShowRouteForwardingtableIpv6Ipv6PrefixDecipher.
    """

    def setUp(self):
        self.cli_output = (
            "NCP-ID: 0\r\n"
            "VRF: default\r\n"
            "IPv6 Forwarding Table:\r\n"
            "Destination: 2001:558:4c0:0:3000::62/128\r\n"
            "    next-hop(1): fe80::8640:76ff:fe3b:39ed Active\r\n"
            "    interface: bundle-178\r\n"
            "    Enhanced-Alternate:\r\n"
            "      next-hop: fe80::8640:76ff:feba:2e0d\r\n"
            "      interface: bundle-349"
        )
        self.decipher = ShowRouteForwardingtableIpv6Ipv6PrefixDecipher()

    def test_decipher(self):
        expected = {
            "destination": "2001:558:4c0:0:3000::62/128",
            "next_hops": [
                {
                    "next_hop": "fe80::8640:76ff:fe3b:39ed",
                    "interface": "bundle-178",
                    "active": True
                }
            ],
            "enhanced_alternate": [
                {
                    "next_hop": "fe80::8640:76ff:feba:2e0d",
                    "interface": "bundle-349"
                }
            ]
        }
        result = self.decipher.decipher(self.cli_output)
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()