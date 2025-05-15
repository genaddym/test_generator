import pytest
import json
import sys
import os

# Adjust sys.path to allow relative import when running pytest directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from show_config_interfaces_INTERFACE_NAME.decipher import ShowConfigInterfacesInterfaceNameDecipher

class TestShowConfigInterfacesInterfaceNameDecipher:
    def test_decipher_bundle_id(self):
        cli_output = (
            "interfaces\n"
            "  ge100-0/0/2/0\n"
            "    admin-state enabled\n"
            "    bundle-id 217\n"
            "    carrier-delay down 0 up 5000\n"
            "    description \"PHY|100G|AGG-MEMBER|CORE|type:JANUS-P2P|rhost:ar-vc01.site50.cran1|rport:ge100-0/0/22|lagg:de217|ragg:de217\"\n"
            "    fec rs-fec-544-514\n"
            "  !\n"
            "!\n"
        )
        expected_output = '{"bundle_id": 217}'
        result = ShowConfigInterfacesInterfaceNameDecipher.decipher(cli_output)
        assert json.dumps(result) == expected_output