import pytest
from .decipher import ShowLldpNeighborsDecipher

class TestShowLldpNeighborsDecipher:
    cli_output_example = (
        "Interface     | Neighbor System Name          | Neighbor interface   | Neighbor TTL   |\n"
        "-------------+-------------------------------+----------------------+----------------|\n"
        "ge100-0/0/2/0 | arvc01.site50.cran1           | ge100-0/0/22         | 120            |\n"
        "ge100-0/0/2/1 | arvc01.site50.cran1           | ge100-0/0/21         | 120            |\n"
        "ge10-0/0/3/0  | ar01.site50.cran1.comcast.net | xe-0/2/2             | 120            |\n"
        "ge10-0/0/3/1  | ar01.site50.cran1.comcast.net | xe-0/2/3             | 120            |\n"
        "ge400-0/0/25  | tcr02.site10.cran1            | ge400-0/0/33         | 120            |\n"
        "ge400-0/0/26  | tcr02.site10.cran1            | ge400-0/0/34         | 120            |\n"
        "ge400-0/0/27  |                               |                      |                |\n"
        "ge400-0/0/28  |                               |                      |                |\n"
        "ge400-0/0/33  | tcr01.site10.cran1            | ge400-0/0/33         | 120            |\n"
        "ge400-0/0/34  | tcr01.site10.cran1            | ge400-0/0/34         | 120            |\n"
    )

    expected_output = {"neighbors": [{"interface": "ge100-0/0/2/0", "neighbor_system_name": "arvc01.site50.cran1", "neighbor_interface": "ge100-0/0/22", "neighbor_ttl": "120"}, {"interface": "ge100-0/0/2/1", "neighbor_system_name": "arvc01.site50.cran1", "neighbor_interface": "ge100-0/0/21", "neighbor_ttl": "120"}, {"interface": "ge10-0/0/3/0", "neighbor_system_name": "ar01.site50.cran1.comcast.net", "neighbor_interface": "xe-0/2/2", "neighbor_ttl": "120"}, {"interface": "ge10-0/0/3/1", "neighbor_system_name": "ar01.site50.cran1.comcast.net", "neighbor_interface": "xe-0/2/3", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/25", "neighbor_system_name": "tcr02.site10.cran1", "neighbor_interface": "ge400-0/0/33", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/26", "neighbor_system_name": "tcr02.site10.cran1", "neighbor_interface": "ge400-0/0/34", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/27", "neighbor_system_name": "", "neighbor_interface": "", "neighbor_ttl": ""}, {"interface": "ge400-0/0/28", "neighbor_system_name": "", "neighbor_interface": "", "neighbor_ttl": ""}, {"interface": "ge400-0/0/33", "neighbor_system_name": "tcr01.site10.cran1", "neighbor_interface": "ge400-0/0/33", "neighbor_ttl": "120"}, {"interface": "ge400-0/0/34", "neighbor_system_name": "tcr01.site10.cran1", "neighbor_interface": "ge400-0/0/34", "neighbor_ttl": "120"}]}

    def test_decipher(self):
        result = ShowLldpNeighborsDecipher.decipher(self.cli_output_example)
        assert result == self.expected_output