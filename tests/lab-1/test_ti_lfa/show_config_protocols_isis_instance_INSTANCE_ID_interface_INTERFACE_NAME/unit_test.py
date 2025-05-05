import unittest
from decipher import ShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher


class TestShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher(unittest.TestCase):
    """
    Unit test for ShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher.
    Validates parsing of fast-reroute configuration from CLI output example.
    """

    CLI_OUTPUT = (
        "protocols\r\n"
        "  isis\r\n"
        "    instance 33287\r\n"
        "      interface bundle-178\r\n"
        "        authentication md5 password enc-gAAAAABjXXXJlaMZt7SYQ5uMfhR_e18iH5__zx1yTt-w3HqCDO1DTr-n6_JtgtIBIW9NslQ6GVdhF6x9ZbAGHibxnovvS3fa2g==\r\n"
        "        level level-2\r\n"
        "        network-type point-to-point\r\n"
        "        address-family ipv4-unicast\r\n"
        "          fast-reroute backup-candidate enabled\r\n"
        "          metric level level-2 2000\r\n"
        "        !\r\n"
        "        address-family ipv6-unicast\r\n"
        "          fast-reroute backup-candidate enabled\r\n"
        "          metric level level-2 2000\r\n"
        "        !\r\n"
        "        delay-normalization\r\n"
        "          interval 10\r\n"
        "          offset 0\r\n"
        "        !\r\n"
        "      !\r\n"
        "    !\r\n"
        "  !\r\n"
        "!"
    )

    def setUp(self):
        self.decipher = ShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher()

    def test_decipher_fast_reroute_configuration(self):
        expected = {
            "ipv4-unicast": {
                "fast-reroute backup-candidate": True,
                "metric level": {
                    "level-2": 2000
                }
            },
            "ipv6-unicast": {
                "fast-reroute backup-candidate": True,
                "metric level": {
                    "level-2": 2000
                }
            }
        }
        result = self.decipher.decipher(self.CLI_OUTPUT)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()