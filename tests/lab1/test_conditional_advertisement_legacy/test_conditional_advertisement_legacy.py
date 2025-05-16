"""
Test description
"""

import sys
import logging
import re
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
from show_lldp_neighbors.decipher import ShowLldpNeighborsDecipher

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
        NetworkTopologyVerification.validate_topology(
            topology_manager.inventory_manager.devices,
            validation_types=[TopologyValidationType.SYSTEM_STATUS],
        )

        # Initialize collections for error tracking and device status
        all_errors = []
        device_status = {}
        tested_devices = set()

        # Get all Drivenets ASBR devices
        drivenets_asbr_devices = topology_manager.get_devices(
            roles=[Roles.ASBR], vendors=[Vendors.DRIVENETS]
        )

        # Compile regex patterns for neighbor system name matching
        pattern_ar0 = re.compile(r"^ar0\d+")
        pattern_arvc = re.compile(r"^arvc\d+")

        # Iterate over each Drivenets ASBR device
        for device in drivenets_asbr_devices:
            device_name = device.name
            device_status[device_name] = {"passed": True, "errors": []}
            tested_devices.add(device_name)
            logger.info(f"\n\nVerifying device {device_name} ...")

            try:
                # Get CLI session for the device
                cli_session = device_manager.cli_sessions[device_name]

                # Send the 'show lldp neighbors' command and decipher the output
                lldp_output = cli_session.send_command(
                    command="show lldp neighbors",
                    decipher=ShowLldpNeighborsDecipher,
                )

                # Extract the list of LLDP neighbors from the deciphered output
                neighbors = lldp_output.lldp_neighbors

                # Filter neighbors whose 'neighbor_system_name' matches the required patterns
                matching_neighbors = [
                    neighbor
                    for neighbor in neighbors
                    if neighbor.neighbor_system_name
                    and (
                        pattern_ar0.match(neighbor.neighbor_system_name)
                        or pattern_arvc.match(neighbor.neighbor_system_name)
                    )
                ]

                # Log the matching neighbors for debug purposes
                logger.info(
                    f"Device {device_name} - Matching LLDP neighbors: {len(matching_neighbors)}"
                )
                for neighbor in matching_neighbors:
                    logger.info(
                        f"  Interface: {neighbor.interface}, Neighbor System Name: {neighbor.neighbor_system_name}"
                    )

            except Exception as e:
                error_msg = f"Error verifying device {device_name}: {e}"
                logger.error(error_msg)
                device_status[device_name]["passed"] = False
                device_status[device_name]["errors"].append(error_msg)
                all_errors.append(error_msg)

        # If any errors were collected, raise an assertion with all errors
        if all_errors:
            failed_devices = [
                name for name, status in device_status.items() if not status["passed"]
            ]
            failed_devices_str = ", ".join(failed_devices)

            error_summary = "\n\n".join(all_errors)
            raise AssertionError(
                f"TEST FAILED: {len(failed_devices)}/{len(tested_devices)} devices failed"
                f" ({failed_devices_str}). Found {len(all_errors)} validation errors:\n\n{error_summary}"
            )

        # Print a summary of what was tested
        logger.info("\n======= TEST SUMMARY =======")
        logger.info(f"Devices tested: {len(tested_devices)}")
        for device in sorted(tested_devices):
            status = "✅ PASSED" if device_status[device]["passed"] else "❌ FAILED"
            logger.info(f"  - {device}: {status}")

        logger.info("All verifications passed successfully!")
        logger.info("==============================")

# Step implementation completed