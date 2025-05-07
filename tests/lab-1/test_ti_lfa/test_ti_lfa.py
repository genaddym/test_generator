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
from show_config_protocols_isis.decipher import ShowConfigProtocolsIsisDecipher


logger = logging.getLogger()

DEVICE_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "devices.yml"
TOPOLOGY_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "topology.json"



class TestTiLfa:
    """
    Test description
    """

    @pytest.mark.parametrize(
        [DEVICE_CONFIG, TOPOLOGY_CONFIG],
        [(DEVICE_CONFIG_FILE, TOPOLOGY_CONFIG_FILE)],
        indirect=True,
    )
    def test_ti_lfa(
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

        logger.info("\n\nValidating topology")
        NetworkTopologyVerification.validate_topology(topology_manager.inventory_manager.devices,
                                                      validation_types=[TopologyValidationType.SYSTEM_STATUS])

        devices = topology_manager.get_devices(
            vendors=[Vendors.DRIVENETS],
        )

        # Collection of all validation errors and tracking device failures
        tested_devices = set()
        all_errors = []
        device_status = {}  # Track pass/fail status for each device

        for device in devices:
            device_name = device.name
            device_status[device_name] = {"passed": True, "errors": []}
            tested_devices.add(device_name)
            logger.info(f"\n\nVerifying device {device_name} ...")
            cli_session = device_manager.cli_sessions[device_name]

            instance_id = cli_session.send_command(
                        command=f"show config protocols isis",
                        decipher=ShowConfigProtocolsIsisDecipher,
                    )
            logger.info(f"ISIS instance ID: {instance_id}")

            # Validate TI-LFA for both IPv4 and IPv6
            self._validate_ti_lfa_config(
                device_name=device_name,
                cli_session=cli_session,
                instance_id=instance_id,
                address_family="ipv4-unicast",
                decipher=ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv4unicastTifastrerouteDecipher,
                device_status=device_status,
                all_errors=all_errors
            )

            self._validate_ti_lfa_config(
                device_name=device_name,
                cli_session=cli_session,
                instance_id=instance_id,
                address_family="ipv6-unicast",
                decipher=ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv6unicastTifastrerouteDecipher,
                device_status=device_status,
                all_errors=all_errors
            )

            # Validate TI-LFA operational status
            self._validate_ti_lfa_operational_status(
                device_name=device_name,
                cli_session=cli_session,
                instance_id=instance_id,
                device_status=device_status,
                all_errors=all_errors
            )

            logger.info("Retrieving all ISIS enabled interfaces...")
            interfaces = cli_session.send_command(
                command=f"show isis interfaces",
                decipher=ShowIsisInterfacesDecipher,
            )
            logger.debug(f"ISIS enabled interfaces: {interfaces}")

            for interface in interfaces:
                logger.info(f"Validating TI-LFA configuration for interface {interface}...")
                self._validate_interface_config(
                    device_name=device_name,
                    cli_session=cli_session,
                    instance_id=instance_id,
                    interface=interface,
                    device_status=device_status,
                    all_errors=all_errors
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

    def _validate_ti_lfa_config(
        self,
        device_name: str,
        cli_session,
        instance_id: str,
        address_family: str,
        decipher,
        device_status: dict,
        all_errors: list
    ):
        """
        Validate TI-LFA configuration for a given address family.

        :param device_name: Name of the device being tested
        :param cli_session: CLI session for the device
        :param instance_id: ISIS instance ID
        :param address_family: Address family to validate (ipv4-unicast or ipv6-unicast)
        :param decipher: Decipher class to use for parsing the output
        :param device_status: Dictionary tracking device status
        :param all_errors: List to collect all validation errors
        """
        logger.info(f"Validate that TI-LFA is configured for {address_family} under the ISIS {instance_id}...")
        ti_lfa_config = cli_session.send_command(
            command=f"show config protocols isis instance {instance_id} address-family {address_family} ti-fast-reroute",
            decipher=decipher,
        )

        # Validate TI-LFA configuration
        if ti_lfa_config.get('admin_state') != 'enabled':
            error_msg = f"Device {device_name}: TI-LFA admin-state is not enabled for {address_family}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        if ti_lfa_config.get('protection_mode') != 'link':
            error_msg = f"Device {device_name}: TI-LFA protection-mode is not set to 'link' for {address_family}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        logger.info(f"TI-LFA {address_family} configuration validated successfully")

    def _validate_interface_config(
        self,
        device_name: str,
        cli_session,
        instance_id: str,
        interface: str,
        device_status: dict,
        all_errors: list,
    ):
        """
        Validate fast-reroute backup-candidate configuration for an interface.

        :param device_name: Name of the device being tested
        :param cli_session: CLI session for the device
        :param instance_id: ISIS instance ID
        :param interface: Interface name to validate
        :param device_status: Dictionary tracking device status
        :param all_errors: List to collect all validation errors
        """
        logger.info(f"Validating fast-reroute configuration for interface {interface}...")
        interface_config = cli_session.send_command(
            command=f"show config protocols isis instance {instance_id} interface {interface}",
            decipher=ShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher,
        )

        # Validate IPv4 configuration
        ipv4_config = interface_config.get("ipv4-unicast", {})
        if not ipv4_config.get("fast-reroute backup-candidate", False):
            error_msg = f"Device {device_name}: Fast-reroute backup-candidate is not enabled for IPv4 on interface {interface}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        # Validate IPv6 configuration
        ipv6_config = interface_config.get("ipv6-unicast", {})
        if not ipv6_config.get("fast-reroute backup-candidate", False):
            error_msg = f"Device {device_name}: Fast-reroute backup-candidate is not enabled for IPv6 on interface {interface}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        logger.info(f"Fast-reroute configuration validated successfully for interface {interface}")

    def _validate_ti_lfa_operational_status(
        self,
        device_name: str,
        cli_session,
        instance_id: str,
        device_status: dict,
        all_errors: list,
    ):
        """
        Validate TI-LFA operational status in ISIS instance.

        :param device_name: Name of the device being tested
        :param cli_session: CLI session for the device
        :param instance_id: ISIS instance ID
        :param device_status: Dictionary tracking device status
        :param all_errors: List to collect all validation errors
        """
        logger.info(f"Validating TI-LFA operational status for ISIS instance {instance_id}...")
        ti_lfa_status = cli_session.send_command(
            command=f"show isis instance {instance_id}",
            decipher=ShowIsisInstanceInstanceIdDecipher,
        )

        # Validate IPv4 TI-LFA status
        ipv4_status = ti_lfa_status.get("IPv4", {})
        if ipv4_status.get("status") != "enabled":
            error_msg = f"Device {device_name}: TI-LFA is not enabled for IPv4"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)
        elif not ipv4_status.get("link-protection", False):
            error_msg = f"Device {device_name}: TI-LFA link-protection is not enabled for IPv4"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        # Validate IPv6 TI-LFA status
        ipv6_status = ti_lfa_status.get("IPv6", {})
        if ipv6_status.get("status") != "enabled":
            error_msg = f"Device {device_name}: TI-LFA is not enabled for IPv6"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)
        elif not ipv6_status.get("link-protection", False):
            error_msg = f"Device {device_name}: TI-LFA link-protection is not enabled for IPv6"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)

        logger.info(f"TI-LFA operational status validated successfully for ISIS instance {instance_id}")
