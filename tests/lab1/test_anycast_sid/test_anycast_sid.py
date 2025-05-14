"""
Anycast SID Test
"""

import re
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass

import pytest

from orbital.testing.common.roles import Roles
from orbital.testing.common.vendors import Vendors
from orbital.testing.device_manager import DeviceManager
from orbital.testing.topology.topology_manager import TopologyManager

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.absolute()))

from orbital.tests.conftest import DEVICE_CONFIG, TOPOLOGY_CONFIG
from orbital.testing.data_objects.bgp_list import (
    RegexConfig,
    PassesThroughConfig,
)
from orbital.testing.data_objects.routing_policy_config import (
    ASPathMatch,
    LargeCommunityMatch,
)
from orbital.testing.helpers.deciphers.drivenets.show_bgp_list import (
    ShowBgpListDecipher,
)
from orbital.testing.helpers.deciphers.drivenets.show_bgp_route import (
    ShowBgpRouteDecipher,
)
from orbital.testing.helpers.deciphers.drivenets.routing_policy_config import (
    RoutingPolicyConfigDecipher,
)
from orbital.testing.topology.topology_validators.topology_validation_types import (
    TopologyValidationType,
)
from orbital.testing.topology.topology_validators.network_topology_verification import (
    NetworkTopologyVerification,
)

logger = logging.getLogger()

DEVICE_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "devices.yml"
TOPOLOGY_CONFIG_FILE = Path("lab-1") / "resources" / "lab-8.1" / "topology.json"
PREFIX_FILE = "test_prefixes.json"

TEST_ROUTING_POLICY_IPV4 = "IPV4-U-RR-SERVER-OUT"
TEST_ROUTING_POLICY_IPV6 = "IPV6-U-RR-SERVER-OUT"
TEST_ROUTING_POLICY_RULES_V4 = [40, 50, 60]
TEST_ROUTING_POLICY_RULES_V6 = [30, 40, 50]


@dataclass
class RuleData:
    """
    Data class to hold rule data for this test.
    """

    rule_number: int
    as_path_regex: str
    large_community: str
    next_hop: str
    address_family: str


class TestAnycastSid:
    """
    Anycast SID Test suite for validating BGP routes and segment routing configuration.

    This test suite verifies that anycast SIDs are correctly configured and advertised
    across the network. It checks both IPv4 and IPv6 prefixes on PCR devices, validating
    BGP path attributes and ensuring route consistency.
    """

    def verify_device_rules_consistency(self, all_devices_rules):
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
    def test_segment_routing(
        self, device_manager: DeviceManager, topology_manager: TopologyManager
    ):
        """
        Anycast SID Test - checks BGP routes for both IPv4 and IPv6 prefixes.

        :param device_manager: Manager for device interactions
        :type device_manager: DeviceManager
        :param topology_manager: Manager for topology operations
        :type topology_manager: TopologyManager
        :raises AssertionError: If validation of BGP routes fails
        :return: None
        """
        logger.info("\n\nValidating topology")
        NetworkTopologyVerification.validate_topology(topology_manager.inventory_manager.devices,
                                                      validation_types=[TopologyValidationType.SYSTEM_STATUS])

        logger.info("\n\nCollecting ASBR data")
        asbrs_data = self._collect_asbr_data(device_manager, topology_manager)

        logger.info("\n\nVerifying PCR devices")
        drivenets_pcrs = topology_manager.get_devices(
            roles=[Roles.PCR],
            vendors=[Vendors.DRIVENETS],
        )

        # Read prefixes from the JSON file
        prefixes = self._load_prefixes_from_file(PREFIX_FILE)
        logger.debug(f"Loaded prefixes for testing: {prefixes}")

        # Statistics counters for summary
        tested_devices = set()
        ipv4_prefixes_tested = set()
        ipv6_prefixes_tested = set()

        # Collection of all validation errors and tracking device failures
        all_errors = []
        device_status = {}  # Track pass/fail status for each device

        # Test all devices and collect errors instead of stopping at the first error
        for device in drivenets_pcrs:
            device_name = device.name
            device_status[device_name] = {"passed": True, "errors": []}
            tested_devices.add(device_name)
            logger.info(f"\n\nVerifying PCR device {device_name} ...")
            cli_session = device_manager.cli_sessions[device_name]

            for af in ["ipv4", "ipv6"]:
                # Track prefixes by address family
                af_prefixes = prefixes.get(f"{af}_prefixes", [])
                if af == "ipv4":
                    ipv4_prefixes_tested.update(af_prefixes)
                else:
                    ipv6_prefixes_tested.update(af_prefixes)

                for prefix in af_prefixes:
                    bgp_route = cli_session.send_command(
                        command=f"show bgp route {prefix}",
                        decipher=ShowBgpRouteDecipher,
                    )

                    # Verify the route but don't raise assertion error immediately
                    success, error_message = self._verify_bgp_route(
                        device_name, bgp_route, prefix, asbrs_data
                    )
                    if not success:
                        all_errors.append(error_message)
                        device_status[device_name]["passed"] = False
                        device_status[device_name]["errors"].append(
                            f"Failed for prefix {prefix}: {error_message}"
                        )

            # Report device status
            if device_status[device_name]["passed"]:
                logger.info(f"✅ Device {device_name} passed all verifications")
            else:
                logger.error(f"❌ Device {device_name} FAILED verification")
                for error in device_status[device_name]["errors"]:
                    logger.error(f"  - {error}")

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

        # Print a summary of what was tested
        logger.info("\n======= TEST SUMMARY =======")
        logger.info(f"Devices tested: {len(tested_devices)}")
        for device in sorted(tested_devices):
            status = "✅ PASSED" if device_status[device]["passed"] else "❌ FAILED"
            logger.info(f"  - {device}: {status}")

        logger.info(f"IPv4 prefixes tested: {len(ipv4_prefixes_tested)}")
        for prefix in sorted(ipv4_prefixes_tested):
            logger.info(f"  - {prefix}")

        logger.info(f"IPv6 prefixes tested: {len(ipv6_prefixes_tested)}")
        for prefix in sorted(ipv6_prefixes_tested):
            logger.info(f"  - {prefix}")

        logger.info("All verifications passed successfully!")
        logger.info("==============================")

    def _load_prefixes_from_file(self, file_path):
        """
        Load prefixes from a JSON file.

        :param file_path: Path to the JSON file containing prefixes
        :type file_path: str
        :raises FileNotFoundError: If the file is not found
        :raises json.JSONDecodeError: If the file is not valid JSON
        :return: Dictionary with IPv4 and IPv6 prefixes
        :rtype: dict
        """
        try:
            with open(str((Path(__file__).parent / file_path).absolute()), "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading prefixes file: {e}")
            raise

    def _verify_bgp_route(self, device_name, bgp_route, prefix, asbrs_data):
        """
        Verify BGP route information.

        :param device_name: Name of the device being checked
        :type device_name: str
        :param bgp_route: BGP route entry
        :type bgp_route: object
        :param prefix: IP prefix being checked
        :type prefix: str
        :param asbrs_data: Data collected from ASBRs
        :type asbrs_data: dict
        :return: Tuple containing success status and error message
        :rtype: tuple(bool, str)
        """
        errors = []

        if bgp_route.total_paths < 2:
            return (
                False,
                f"{device_name}: Only {bgp_route.total_paths} paths found for prefix {prefix}",
            )

        # Determine if this is an IPv4 or IPv6 prefix
        address_family = "ipv6" if ":" in prefix else "ipv4"

        # Get the first ASBR rules, since they are the same across ASBRs
        all_asbr_rules = list(asbrs_data.values())[0]

        # Filter rules by address family
        asbr_rules = [
            rule for rule in all_asbr_rules if rule.address_family == address_family
        ]

        # Verify only the first 2 BGP paths
        for path_index, path in enumerate(bgp_route.paths[:2]):
            if not path.attributes or not path.attributes.as_path:
                errors.append(
                    f"{device_name}: Path {path_index+1} has no attributes or AS path"
                )
                continue

            if not path.attributes.as_path[0].asns:
                errors.append(f"{device_name}: Path {path_index+1} has empty AS path")
                continue

            first_as = path.attributes.as_path[0].asns[0]  # e.g "4200001220"

            if not path.valid:
                errors.append(
                    f"{device_name}: Path {path_index+1} should be valid but is not"
                )

            # Verify path #1 is valid, internal, best
            if path_index == 0:
                if not path.best:
                    errors.append(f"{device_name}: Path #1 should be best but is not")
                if path.backup:
                    errors.append(
                        f"{device_name}: Path #1 should not be backup but it is"
                    )

            # Verify path #2 is valid, internal, backup
            elif path_index == 1:
                if not path.backup:
                    errors.append(f"{device_name}: Path #2 should be backup but is not")
                if path.best:
                    errors.append(
                        f"{device_name}: Path #2 should not be best but it is"
                    )

        # Skip further checks if we already have validation errors on the paths
        if errors:
            error_details = "\n".join(errors)
            return False, error_details

        # Now check if any path matches any rule
        rule_match_found = False
        for path_index, path in enumerate(bgp_route.paths[:2]):
            first_as = path.attributes.as_path[0].asns[0]

            for rule in asbr_rules:  # Using filtered rules by address family
                # Handle the case where the regex ends with '_' but the AS number doesn't have it
                as_path_regex = rule.as_path_regex

                # Check if all of these match:
                # 1. AS path regex matches the first AS
                # 2. Next hop matches
                # 3. Communities match (either standard or large)
                if (
                    as_path_regex
                    and first_as
                    and
                    # Use a proper regex check that matches the pattern correctly
                    # If the regex ends with '_' but the AS doesn't have it, adjust the comparison
                    (
                        re.match(as_path_regex, first_as)
                        or (
                            as_path_regex.endswith("_")
                            and re.match(as_path_regex[:-1] + "$", first_as)
                        )
                    )
                    and rule.next_hop == path.next_hop
                ):

                    # Check communities if they exist in the rule and path
                    community_match = False

                    # If the rule has a large community defined
                    if rule.large_community:
                        # Check if path has large communities defined and if any match the rule
                        if (
                            path.attributes.communities
                            and path.attributes.communities.large
                            and rule.large_community
                            in path.attributes.communities.large
                        ):
                            community_match = True
                        # Check standard communities as a fallback
                        elif (
                            path.attributes.communities
                            and path.attributes.communities.standard
                            and rule.large_community
                            in path.attributes.communities.standard
                        ):
                            community_match = True

                    # If the rule doesn't have a large community or if no match yet
                    if not rule.large_community or not community_match:
                        # Consider it a match if rule doesn't have a community requirement
                        community_match = not rule.large_community

                    # Rule matches if both AS path and communities match
                    if community_match:
                        # This is a simplification, as the test is not vendor-agnostic
                        # if any of 2 paths are valid, the test is considered successful
                        rule_match_found = True
                        break

            if rule_match_found:
                break

        if rule_match_found:
            return True, ""

        # If we get here, no rule was matched
        # Build detailed error message for troubleshooting
        error_msg = f"\nNo matching rule found for prefix {prefix} on {device_name}:"
        for i, path in enumerate(bgp_route.paths[:2]):
            error_msg += f"\n  Path #{i+1}:"
            error_msg += f"\n    Status: {'Best' if path.best else ''}{'Backup' if path.backup else ''}"
            error_msg += f"\n    Valid: {path.valid}"
            error_msg += f"\n    Next Hop: {path.next_hop}"
            if path.attributes and path.attributes.as_path:
                as_path = "->".join(
                    [
                        str(asn)
                        for segment in path.attributes.as_path
                        for asn in segment.asns
                    ]
                )
                error_msg += f"\n    AS Path: {as_path}"
            if path.attributes and path.attributes.communities:
                if path.attributes.communities.large:
                    error_msg += f"\n    Large Communities: {', '.join(path.attributes.communities.large)}"
                if path.attributes.communities.standard:
                    error_msg += f"\n    Standard Communities: {', '.join(path.attributes.communities.standard)}"

        return False, error_msg

    def _collect_asbr_data(
        self, device_manager: DeviceManager, topology_manager: TopologyManager
    ):
        """
        Collect and verify data from ASBR devices for both IPv4 and IPv6.

        Args:
            device_manager: The device manager instance
            topology_manager: The topology manager instance

        Returns:
            A dictionary containing the rules data for each ASBR device
        """
        drivenets_asbrs = topology_manager.get_devices(
            roles=[Roles.ASBR],
            vendors=[Vendors.DRIVENETS],
        )

        all_devices_rules = {}

        # Define address families to process
        address_families = [
            {"name": "ipv4", "policy": TEST_ROUTING_POLICY_IPV4},
            {"name": "ipv6", "policy": TEST_ROUTING_POLICY_IPV6},
        ]

        for device in drivenets_asbrs:
            logger.info(f"\n\nVerifying ASBR device {device.name} ...")
            cli_session = device_manager.cli_sessions[device.name]

            device_rules_data = []

            # Process both IPv4 and IPv6 policies
            for af in address_families:
                policy_config = cli_session.send_command(
                    command=f"show config routing-policy policy {af['policy']}",
                    decipher=RoutingPolicyConfigDecipher,
                )

                test_routing_policy_rules = (
                    TEST_ROUTING_POLICY_RULES_V4
                    if af["name"] == "ipv4"
                    else TEST_ROUTING_POLICY_RULES_V6
                )
                for rule_number in test_routing_policy_rules:
                    assert (
                        rule_number
                        in policy_config.routing_policies[af["policy"]].rules
                    ), f"Rule {rule_number} not found in policy {af['policy']} on device {device.name}"

                    rule = policy_config.routing_policies[af["policy"]].rules[
                        rule_number
                    ]
                    rule_data = RuleData(
                        rule_number=rule_number,
                        as_path_regex="",
                        large_community="",
                        next_hop="",
                        address_family=af["name"],
                    )

                    for match in rule.match_conditions:
                        cmd = ""
                        if isinstance(match, ASPathMatch):
                            cmd = f"show as-path-list {match.as_path}"
                            rule_data.next_hop = rule.set_actions[0].next_hop
                        elif isinstance(match, LargeCommunityMatch):
                            cmd = f"show large-community-list {match.large_community}"
                            rule_data.next_hop = rule.set_actions[0].next_hop
                        else:
                            raise ValueError(
                                f"Unexpected match condition type: {type(match)} in rule {rule_number}"
                            )

                        bgp_list_rules = cli_session.send_command(
                            command=cmd, decipher=ShowBgpListDecipher
                        )
                        assert (
                            len(bgp_list_rules.bgp_rules) == 1
                        ), f"Expected 1 rule in {cmd}, but found {len(bgp_list_rules.bgp_rules)}"
                        rule_config = bgp_list_rules.bgp_rules[0].config_items
                        if isinstance(rule_config.as_type, PassesThroughConfig):
                            rule_data.large_community = (
                                rule_config.as_type.as_number_limit
                            )
                        elif isinstance(rule_config.as_type, RegexConfig):
                            rule_data.as_path_regex = rule_config.as_type.as_regex
                        else:
                            raise ValueError(
                                f"Unexpected as_type: {type(rule_config.as_type)} in rule {rule_number}"
                            )

                    device_rules_data.append(rule_data)

            all_devices_rules[device.name] = device_rules_data

        # Verify IPv4 and IPv6 rules separately
        self._verify_device_rules_by_address_family(all_devices_rules)

        logger.info(
            f"Successfully verified that all ASBR devices have identical rule configurations"
        )

        # Pretty-print the rules data for better readability
        logger.info("\nCollected ASBR rules data:")

        # Group rules by address family
        ipv4_rules = [
            r for r in list(all_devices_rules.values())[0] if r.address_family == "ipv4"
        ]
        ipv6_rules = [
            r for r in list(all_devices_rules.values())[0] if r.address_family == "ipv6"
        ]

        # Print IPv4 rules
        logger.info("IPv4 Rules:")
        for rule in ipv4_rules:
            self._print_rule_data(rule, prefix="  ")

        # Print IPv6 rules
        logger.info("IPv6 Rules:")
        for rule in ipv6_rules:
            self._print_rule_data(rule, prefix="  ")

        return all_devices_rules

    def _verify_device_rules_by_address_family(self, all_devices_rules):
        """
        Verify that all devices have identical rule configurations, separated by address family.

        Args:
            all_devices_rules: Dictionary mapping device names to their rule configurations

        Returns:
            None: Raises assertion error if inconsistencies are found
        """
        device_names = list(all_devices_rules.keys())

        # Skip verification if there's only one device
        if len(device_names) <= 1:
            logger.debug(
                "Only one device found, skipping rule consistency verification"
            )
            return

        # Separate rules by address family for each device
        for af in ["ipv4", "ipv6"]:
            logger.info(f"Verifying {af.upper()} rules consistency across devices")

            # For each device, get only rules for current address family
            first_device_af_rules = [
                r for r in all_devices_rules[device_names[0]] if r.address_family == af
            ]

            for i in range(1, len(device_names)):
                current_device = device_names[i]
                current_af_rules = [
                    r
                    for r in all_devices_rules[current_device]
                    if r.address_family == af
                ]

                assert len(first_device_af_rules) == len(current_af_rules), (
                    f"Number of {af.upper()} rules mismatch: {device_names[0]} has {len(first_device_af_rules)} rules, "
                    f"but {current_device} has {len(current_af_rules)} rules"
                )

                for j, (base_rule, curr_rule) in enumerate(
                    zip(first_device_af_rules, current_af_rules)
                ):
                    assert base_rule.rule_number == curr_rule.rule_number, (
                        f"{af.upper()} rule number mismatch at index {j}: {device_names[0]} has rule number {base_rule.rule_number}, "
                        f"but {current_device} has rule number {curr_rule.rule_number}"
                    )
                    assert base_rule.as_path_regex == curr_rule.as_path_regex, (
                        f"{af.upper()} AS path regex mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.as_path_regex}', "
                        f"but {current_device} has '{curr_rule.as_path_regex}'"
                    )
                    assert base_rule.large_community == curr_rule.large_community, (
                        f"{af.upper()} Large community mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.large_community}', "
                        f"but {current_device} has '{curr_rule.large_community}'"
                    )
                    assert base_rule.next_hop == curr_rule.next_hop, (
                        f"{af.upper()} Next hop mismatch for rule {base_rule.rule_number}: {device_names[0]} has '{base_rule.next_hop}', "
                        f"but {current_device} has '{curr_rule.next_hop}'"
                    )

            logger.info(
                f"Successfully verified that all {len(device_names)} devices have identical {af.upper()} rule configurations"
            )

    def _print_rule_data(self, rule, prefix=""):
        """
        Helper method to print formatted rule data with an optional prefix.

        Args:
            rule: The RuleData object to print
            prefix: Optional prefix string to add before each line (e.g., indentation)
        """
        logger.info(f"{prefix}Rule #{rule.rule_number}:")
        logger.info(f"{prefix}  AS Path Regex: {rule.as_path_regex}")
        logger.info(f"{prefix}  Large Community: {rule.large_community or 'None'}")
        logger.info(f"{prefix}  Next Hop: {rule.next_hop}")
