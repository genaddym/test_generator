import unittest
from decipher import ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv6unicastTifastrerouteDecipher

class TestShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv6unicastTifastrerouteDecipher(unittest.TestCase):
    def test_decipher(self):
        cli_output = "protocols\r\n  isis\r\n    instance INSTANCE_ID\r\n      address-family ipv6-unicast\r\n        ti-fast-reroute\r\n          admin-state enabled\r\n          protection-mode link"
        expected_result = {
            'admin-state': 'enabled',
            'protection-mode': 'link'
        }
        decipher = ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv6unicastTifastrerouteDecipher()
        self.assertEqual(decipher.decipher(cli_output), expected_result)

if __name__ == '__main__':
    unittest.main()