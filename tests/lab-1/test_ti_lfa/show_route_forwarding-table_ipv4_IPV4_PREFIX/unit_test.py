import unittest
from decipher import ShowRouteForwardingtableIpv4Ipv4PrefixDecipher

class TestShowRouteForwardingtableIpv4Ipv4PrefixDecipher(unittest.TestCase):
    """
    Unit test for ShowRouteForwardingtableIpv4Ipv4PrefixDecipher.
    """

    def setUp(self):
        self.cli_output = (
            "NCP-ID: 0\r\n"
            "VRF: default\r\n"
            "IPv4 Forwarding Table:\r\n"
            "Destination: 96.109.183.86/32\r\n"
            "    next-hop(1): 96.217.0.229 Active\r\n"
            "    interface: bundle-178\r\n"
            "    Enhanced-Alternate:\r\n"
            "      next-hop: 96.217.1.202\r\n"
            "      interface: bundle-349"
        )
        self.decipher = ShowRouteForwardingtableIpv4Ipv4PrefixDecipher()

    def test_decipher(self):
        expected = {
            'forwarding-table': {
                'destination': '96.109.183.86/32',
                'next-hops': [
                    {
                        'next-hop': '96.217.0.229',
                        'active': True,
                        'interface': 'bundle-178'
                    }
                ],
                'enhanced-alternate': {
                    'next-hop': '96.217.1.202',
                    'interface': 'bundle-349'
                }
            }
        }
        result = self.decipher.decipher(self.cli_output)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()