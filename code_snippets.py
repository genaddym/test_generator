# example of getting devices by vendor
drivenets_devices = topology_manager.get_devices(
    vendors=[Vendors.DRIVENETS],
)

# example of getting devices by role and vendor
drivenets_pcrs = topology_manager.get_devices(
    roles=[Roles.PCR],
    vendors=[Vendors.DRIVENETS],
)

# example of iterating over devices
for device in drivenets_pcrs:
    # example of sending a command and deciphering the output
    cli_session = device_manager.cli_sessions[device.name]
    bgp_route = cli_session.send_command(
                command=f"show bgp route {prefix}",
                decipher=ShowBgpRouteDecipher,
            )

    # example of configuring a device
    cli_session.edit_config(f"interfaces {interface_name} admin-state enabled"
        
    )


# example of using IXIA
# IMPORTANT: traffic manager fixture should be used for executing IXIA commands
# reset_ixia fixture should be used as well in all tests that involve IXIA for resetting IXIA before the test

# example of using IXIA auxiliary functions
from tests.common.ixia import (
    CompareType,
    validate_no_traffic_loss,
    validate_packet_loss_duration,
)

# example of using IXIA connection
ix_conn = traffic_manager.connection
if not ix_conn:
    error_msg = (
        "Traffic generator is not connected. "
    )
    raise AssertionError(error_msg)

# example of enabling/disabling traffic items
ix_conn.enable_disable_all_traffic_items(enable=False)
ix_conn.enable_disable_traffic_item_by_name(
    list_of_trafficItemName=self.TRAFFIC_ITEM_NAMES, enable=True
)

# example of starting/stopping traffic
ix_conn.start_traffic(with_capture=True)
ix_conn.stop_traffic()

# example of validating traffic statistics
validate_no_traffic_loss(ix_conn, clear_stats=False)


# Collection of all validation errors and tracking device failures
tested_devices = set()
all_errors = []
device_status = {}  # Track pass/fail status for each device

# Test all devices and collect errors instead of stopping at the first error
for device in drivenets_pcrs:
    device_name = device.name
    device_status[device_name] = {"passed": True, "errors": []}
    tested_devices.add(device_name)
    logger.info(f"\n\nVerifying device {device_name} ...")
    # device verification code here

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