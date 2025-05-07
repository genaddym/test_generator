"""
Test description
"""

import sys
import logging
from pathlib import Path
import random
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

RANDOM_PREFIXES_COUNT = 10

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
                        command="show config protocols isis",
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

            # Get random prefixes for validation
            selected_prefixes = self._get_random_prefixes(
                device_name=device_name,
                cli_session=cli_session,
                instance_id=instance_id
            )

            # Validate forwarding table entries for IPv4 prefixes
            for prefix in selected_prefixes["ipv4"]:
                self._validate_forwarding_table_entry(
                    device_name=device_name,
                    cli_session=cli_session,
                    prefix=prefix,
                    address_family="ipv4",
                    device_status=device_status,
                    all_errors=all_errors
                )

            # Validate forwarding table entries for IPv6 prefixes
            for prefix in selected_prefixes["ipv6"]:
                self._validate_forwarding_table_entry(
                    device_name=device_name,
                    cli_session=cli_session,
                    prefix=prefix,
                    address_family="ipv6",
                    device_status=device_status,
                    all_errors=all_errors
                )

            logger.info(f"{device_name}: Retrieving all ISIS enabled interfaces...")
            interfaces = cli_session.send_command(
                command="show isis interfaces",
                decipher=ShowIsisInterfacesDecipher,
            )
            logger.debug(f"ISIS enabled interfaces: {interfaces}")

            for interface in interfaces:
                logger.info(f"{device_name}: Validating TI-LFA configuration for interface {interface}...")
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
        logger.info(f"{device_name}: Validating TI-LFA configuration for {address_family} under the ISIS {instance_id}...")
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

        logger.info(f"{device_name}: TI-LFA {address_family} configuration validated successfully")

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
        logger.info(f"{device_name}: Validating fast-reroute configuration for interface {interface}...")
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

        logger.info(f"{device_name}: Fast-reroute configuration validated successfully for interface {interface}")

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
        logger.info(f"{device_name}: Validating TI-LFA operational status for ISIS instance {instance_id}...")
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

        logger.info(f"{device_name}: TI-LFA operational status validated successfully for ISIS instance {instance_id}")

    def _get_random_prefixes(
        self,
        device_name: str,
        cli_session,
        instance_id: str,
    ) -> dict:
        """
        Retrieve random prefixes from ISIS route table for each address family.

        :param device_name: Name of the device being tested
        :param cli_session: CLI session for the device
        :param instance_id: ISIS instance ID
        :return: Dictionary with IPv4 and IPv6 prefixes
        """
        logger.info(f"{device_name}: Retrieving random {RANDOM_PREFIXES_COUNT} prefixes from ISIS route table for instance {instance_id}...")
        route_table = cli_session.send_command(
            command=f"show isis route table mpls-sr",
            decipher=ShowIsisRouteTableMplssrDecipher,
        )

        # Get routes for the current instance
        instance_routes = route_table.get(instance_id, {})
        
        # Get prefixes for each address family
        ipv4_routes = instance_routes.get("ipv4", [])
        ipv6_routes = instance_routes.get("ipv6", [])

        # Select random prefixes
        selected_prefixes = {
            "ipv4": [],
            "ipv6": []
        }

        # Select random IPv4 prefixes
        if ipv4_routes:
            # Get unique prefixes
            ipv4_prefixes = {route["prefix"] for route in ipv4_routes if route.get("prefix")}
            # Select random prefixes
            selected_ipv4 = random.sample(list(ipv4_prefixes), min(RANDOM_PREFIXES_COUNT, len(ipv4_prefixes)))
            selected_prefixes["ipv4"] = selected_ipv4

        # Select random IPv6 prefixes
        if ipv6_routes:
            # Get unique prefixes
            ipv6_prefixes = {route["prefix"] for route in ipv6_routes if route.get("prefix")}
            # Select random prefixes
            selected_ipv6 = random.sample(list(ipv6_prefixes), min(RANDOM_PREFIXES_COUNT, len(ipv6_prefixes)))
            selected_prefixes["ipv6"] = selected_ipv6

        return selected_prefixes

    def _validate_forwarding_table_entry(
        self,
        device_name: str,
        cli_session,
        prefix: str,
        address_family: str,
        device_status: dict,
        all_errors: list,
    ):
        """
        Validate that a prefix has an alternate path in the forwarding table.

        :param device_name: Name of the device being tested
        :param cli_session: CLI session for the device
        :param prefix: The prefix to validate
        :param address_family: Address family (ipv4 or ipv6)
        :param device_status: Dictionary tracking device status
        :param all_errors: List to collect all validation errors
        """
        logger.info(f"{device_name}: Validating forwarding table entry for {address_family} prefix {prefix}...")
        
        # Select appropriate decipher based on address family
        decipher = (
            ShowRouteForwardingtableIpv4Ipv4PrefixDecipher if address_family == "ipv4"
            else ShowRouteForwardingtableIpv6Ipv6PrefixDecipher
        )

        # Get forwarding table entry
        forwarding_entry = cli_session.send_command(
            command=f"show route forwarding-table {address_family} {prefix}",
            decipher=decipher,
        )

        # Validate destination
        if not forwarding_entry.get("destination"):
            error_msg = f"Device {device_name}: No forwarding table entry found for {address_family} prefix {prefix}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)
            return

        # Validate enhanced alternate path
        enhanced_alternate = forwarding_entry.get("enhanced_alternate", [])
        if not enhanced_alternate:
            error_msg = f"Device {device_name}: No enhanced alternate path found for {address_family} prefix {prefix}"
            device_status[device_name]["passed"] = False
            device_status[device_name]["errors"].append(error_msg)
            all_errors.append(error_msg)
            return

        # Validate next-hop and interface for each alternate path
        for alt_path in enhanced_alternate:
            if not alt_path.get("next_hop"):
                error_msg = f"Device {device_name}: Missing next-hop in enhanced alternate path for {address_family} prefix {prefix}"
                device_status[device_name]["passed"] = False
                device_status[device_name]["errors"].append(error_msg)
                all_errors.append(error_msg)
                continue

            if not alt_path.get("interface"):
                error_msg = f"Device {device_name}: Missing interface in enhanced alternate path for {address_family} prefix {prefix}"
                device_status[device_name]["passed"] = False
                device_status[device_name]["errors"].append(error_msg)
                all_errors.append(error_msg)
                continue

            if not alt_path["interface"].startswith("bundle-"):
                error_msg = f"Device {device_name}: Enhanced alternate interface {alt_path['interface']} is not a bundle for {address_family} prefix {prefix}"
                device_status[device_name]["passed"] = False
                device_status[device_name]["errors"].append(error_msg)
                all_errors.append(error_msg)
                continue

        logger.info(f"{device_name}: Forwarding table entry validated successfully for {address_family} prefix {prefix}")
