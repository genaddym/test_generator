import unittest
from decipher import ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv4unicastTifastrerouteDecipher

class TestShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv4unicastTifastrerouteDecipher(unittest.TestCase):
    def test_decipher(self):
        cli_output = "protocols\r\n  isis\r\n    instance INSTANCE_ID\r\n      address-family ipv4-unicast\r\n        ti-fast-reroute\r\n          admin-state enabled\r\n          protection-mode link"
        expected_result = {
            'admin_state': 'enabled',
            'protection_mode': 'link'
        }
        decipher = ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv4unicastTifastrerouteDecipher()
        result = decipher.decipher(cli_output)
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()