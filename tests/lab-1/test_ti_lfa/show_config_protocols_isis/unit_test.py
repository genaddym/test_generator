import unittest
from decipher import ShowConfigProtocolsIsisDecipher

class TestShowConfigProtocolsIsisDecipher(unittest.TestCase):
    """
    Unit test for ShowConfigProtocolsIsisDecipher.
    """

    def setUp(self):
        self.decipher = ShowConfigProtocolsIsisDecipher()
        self.cli_output = (
            "protocols\r\n"
            "  isis\r\n"
            "    maximum-adjacencies 500 threshold 75\r\n"
            "    maximum-routes 1000000 threshold 75\r\n"
            "    nsr enabled\r\n"
            "    instance 33287"
        )

    def test_decipher_returns_correct_instance_id(self):
        instance_id = self.decipher.decipher(self.cli_output)
        self.assertIsInstance(instance_id, int)
        self.assertEqual(instance_id, 33287)

    def test_decipher_returns_none_if_instance_missing(self):
        cli_output_no_instance = (
            "protocols\r\n"
            "  isis\r\n"
            "    maximum-adjacencies 500 threshold 75\r\n"
            "    maximum-routes 1000000 threshold 75\r\n"
            "    nsr enabled"
        )
        instance_id = self.decipher.decipher(cli_output_no_instance)
        self.assertIsNone(instance_id)

if __name__ == "__main__":
    unittest.main()