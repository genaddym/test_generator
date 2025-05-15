"""
Test description
"""

import sys
import logging
from pathlib import Path

import pytest

from orbital.testing.common.roles import Roles
from orbital.testing.common.vendors import Vendors
from orbital.testing.device_manager import DeviceManager
from orbital.testing.topology.topology_manager import TopologyManager

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.absolute()))

from orbital.tests.conftest import DEVICE_CONFIG, TOPOLOGY_CONFIG
from orbital.testing.topology.topology_validators.topology_validation_types import (
    TopologyValidationType,
)
from orbital.testing.topology.topology_validators.network_topology_verification import (
    NetworkTopologyVerification,
)

# Import deciphers and data objects

logger = logging.getLogger()

DEVICE_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "devices.yml"
TOPOLOGY_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "topology.json"



class TestTestConditionalAdvertisementLegacy:
    """
    Test description
    """

    @pytest.mark.parametrize(
        [DEVICE_CONFIG, TOPOLOGY_CONFIG],
        [(DEVICE_CONFIG_FILE, TOPOLOGY_CONFIG_FILE)],
        indirect=True,
    )
    def test_conditional_advertisement_legacy(
        self, device_manager: DeviceManager, topology_manager: TopologyManager
    ):
        """
        Use The Sphinx docstring format for the test description

        [Summary]
        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]

        """

        # always start with a validation of the topology
        logger.info("\n\nValidating topology")
        NetworkTopologyVerification.validate_topology(topology_manager.inventory_manager.devices,
                                                      validation_types=[TopologyValidationType.SYSTEM_STATUS])


        # test logic here
