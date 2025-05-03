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

# Import deciphers and data objects

logger = logging.getLogger()

DEVICE_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "devices.yml"
TOPOLOGY_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "topology.json"



class TestAnycastSid:
    """
    Test description
    """

        """
        Verify that all devices have identical rule configurations.

        :param all_devices_rules: Dictionary mapping device names to their rule configurations
        :type all_devices_rules: dict
        :raises AssertionError: If inconsistencies are found between devices
        :return: None
        """
        device_names = list(all_devices_rules.keys())

        # Skip verification if there's only one device
        if len(device_names) > 1:
            first_device_rules = all_devices_rules[device_names[0]]
            for i in range(1, len(device_names)):
                current_device = device_names[i]
                current_rules = all_devices_rules[current_device]

                assert len(first_device_rules) == len(current_rules), (
                    f"Number of rules mismatch: {device_names[0]} has {len(first_device_rules)} rules, "
                    f"but {current_device} has {len(current_rules)} rules"
                )

                for j, (base_rule, curr_rule) in enumerate(
                    zip(first_device_rules, current_rules)
                ):
                    assert base_rule.rule_number == curr_rule.rule_number, (
                        f"Rule number mismatch at index {j}: {device_names[0]} has rule number {base_rule.rule_number}, "
                        f"but {current_device} has rule number {curr_rule.rule_number}"
                    )
                    assert base_rule.as_path_regex == curr_rule.as_path_regex, (
                        f"AS path regex mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.as_path_regex}', "
                        f"but {current_device} has '{curr_rule.as_path_regex}'"
                    )
                    assert base_rule.large_community == curr_rule.large_community, (
                        f"Large community mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.large_community}', "
                        f"but {current_device} has '{curr_rule.large_community}'"
                    )
                    assert base_rule.next_hop == curr_rule.next_hop, (
                        f"Next hop mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.next_hop}', "
                        f"but {current_device} has '{curr_rule.next_hop}'"
                    )

            logger.info(
                f"Successfully verified that all {len(device_names)} devices have identical rule configurations"
            )
        else:
            logger.info("Only one device found, skipping rule consistency verification")

    @pytest.mark.parametrize(
        [DEVICE_CONFIG, TOPOLOGY_CONFIG],
        [(DEVICE_CONFIG_FILE, TOPOLOGY_CONFIG_FILE)],
        indirect=True,
    )
    def test_template(
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



        # example of getting devices by role and vendor
        drivenets_pcrs = topology_manager.get_devices(
            roles=[Roles.PCR],
            vendors=[Vendors.DRIVENETS],
        )

        # Test all devices and collect errors instead of stopping at the first error
        for device in drivenets_pcrs:
            device_name = device.name
            device_status[device_name] = {"passed": True, "errors": []}
            tested_devices.add(device_name)
            logger.info(f"\n\nVerifying device {device_name} ...")
            cli_session = device_manager.cli_sessions[device_name]

            # example of sending a command and deciphering the output
            bgp_route = cli_session.send_command(
                        command=f"show bgp route {prefix}",
                        decipher=ShowBgpRouteDecipher,
                    )

        # If we collected any errors, raise an assertion with all errors
        if all_errors:
            # Count failed devices
            failed_devices = [
                name for name, status in device_status.items() if not status["passed"]
            ]
            failed_devices_str = ", ".join(failed_devices)

            error_summary = "\n\n".join(all_errors)
            raise AssertionError(
                f"TEST FAILED: {len(failed_devices)}/{len(tested_devices)} devices failed"
                f" ({failed_devices_str}). Found {len(all_errors)} validation errors:\n\n{error_summary}"
            )

        # Example of printing a summary of what was tested
        logger.info("\n======= TEST SUMMARY =======")
        logger.info(f"Devices tested: {len(tested_devices)}")
        for device in sorted(tested_devices):
            status = "✅ PASSED" if device_status[device]["passed"] else "❌ FAILED"
            logger.info(f"  - {device}: {status}")

        logger.info("All verifications passed successfully!")
        logger.info("==============================")
