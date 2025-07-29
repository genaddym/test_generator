"""
Test Description
"""

import logging
import pytest

from orbital.testing.device_manager import DeviceManager
from orbital.testing.topology.topology_manager import TopologyManager
from orbital.testing.common.vendors import Vendors
from orbital.testing.common.roles import Roles

from orbital.testing.topology.topology_validators.topology_validation_types import (
    TopologyValidationType,
)
from orbital.testing.topology.topology_validators.network_topology_verification import (
    NetworkTopologyVerification,
)

# Import deciphers and data objects

logger = logging.getLogger()



@pytest.mark.integration
class TestTemplate:
    """
    Test Description
    """

    def test_template(
        self,
        device_manager: DeviceManager, # pylint: disable=unused-argument
        topology_manager: TopologyManager, # pylint: disable=unused-argument
        request, # pylint: disable=unused-argument
        traffic_manager, # pylint: disable=unused-argument
        reset_ixia  # pylint: disable=unused-argument
    ):
        """

        """
        logger.info("\n\nValidating topology")
        NetworkTopologyVerification.validate_topology(
            topology_manager.inventory_manager.devices,
            validation_types=[TopologyValidationType.SYSTEM_STATUS],
        )


        # test logic here



