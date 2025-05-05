import unittest
from decipher import ShowIsisInterfacesDecipher

class TestShowIsisInterfacesDecipher(unittest.TestCase):
    def test_decipher(self):
        cli_output = "  Instance 33287:\r\n    Interface                                          State    Type           Level\r\n    bundle-178                                         Up       point-to-point L2       \r\n    bundle-247                                         Up       point-to-point L2       \r\n    bundle-349                                         Up       point-to-point L2       \r\n    bundle-352                                         Up       point-to-point L2       \r\n    bundle-355                                         Up       point-to-point L2       \r\n    bundle-742                                         Up       point-to-point L2       \r\n    bundle-745                                         Up       point-to-point L2 "
        expected_result = {
            '33287': [
                {'Interface': 'bundle-178', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-247', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-349', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-352', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-355', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-742', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'},
                {'Interface': 'bundle-745', 'State': 'Up', 'Type': 'point-to-point', 'Level': 'L2'}
            ]
        }
        decipher = ShowIsisInterfacesDecipher()
        self.assertEqual(decipher.decipher(cli_output), expected_result)

if __name__ == '__main__':
    unittest.main()