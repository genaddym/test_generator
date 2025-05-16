import pytest
import sys
import os

# Adjust sys.path to allow relative import of decipher module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from decipher import ShowLldpNeighborsDecipher

class TestShowLldpNeighborsDecipher:
    def test_decipher(self):
        cli_output = '''Interface     | Neighbor System Name          | Neighbor interface   | Neighbor TTL   |
-------------+-------------------------------+----------------------+----------------|
ge100-0/0/2/0 | arvc01.site50.cran1           | ge100-0/0/22         | 120            |
ge100-0/0/2/1 | arvc01.site50.cran1           | ge100-0/0/21         | 120            |
ge10-0/0/3/0  | ar01.site50.cran1.comcast.net | xe-0/2/2             | 120            |
ge10-0/0/3/1  | ar01.site50.cran1.comcast.net | xe-0/2/3             | 120            |
ge400-0/0/25  | tcr02.site10.cran1            | ge400-0/0/33         | 120            |
ge400-0/0/26  | tcr02.site10.cran1            | ge400-0/0/34         | 120            |
ge400-0/0/27  |                               |                      |                |
ge400-0/0/28  |                               |                      |                |
ge400-0/0/33  | tcr01.site10.cran1            | ge400-0/0/33         | 120            |
ge400-0/0/34  | tcr01.site10.cran1            | ge400-0/0/34         | 120            |
'''
        expected_output = {"lldp_neighbors": [{"interface": "ge100-0/0/2/0", "neighbor_system_name": "arvc01.site50.cran1", "neighbor_interface": "ge100-0/0/22", "neighbor_ttl": "120"}, {"interface": "ge100-0/0/2/1", "neighbor_system_name": "arvc01.site50.cran1", "neighbor_interface": "ge100-0/0/21", "neighbor_ttl": "120"}, {"interface": "ge10-0/0/3/0", "neighbor_system_name": "ar01.site50.cran1.comcast.net", "neighbor_interface": "xe-0/2/2", "neighbor_ttl": "120"}, {"interface": "ge10-0/0/3/1", "neighbor_system_name": "ar01.site50.cran1.comcast.net", "neighbor_interface": "xe-0/2/3", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/25", "neighbor_system_name": "tcr02.site10.cran1", "neighbor_interface": "ge400-0/0/33", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/26", "neighbor_system_name": "tcr02.site10.cran1", "neighbor_interface": "ge400-0/0/34", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/27", "neighbor_system_name": "", "neighbor_interface": "", "neighbor_ttl": ""}, {"interface": "ge400-0/0/28", "neighbor_system_name": "", "neighbor_interface": "", "neighbor_ttl": ""}, {"interface": "ge400-0/0/33", "neighbor_system_name": "tcr01.site10.cran1", "neighbor_interface": "ge400-0/0/33", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/34", "neighbor_system_name": "tcr01.site10.cran1", "neighbor_interface": "ge400-0/0/34", "neighbor_ttl": "120"}]}
        output = ShowLldpNeighborsDecipher.decipher(cli_output)
        assert output == expected_output