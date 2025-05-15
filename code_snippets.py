# example of getting devices by vendor
drivenets_devices = topology_manager.get_devices(
    vendors=[Vendors.DRIVENETS],
)

# example of getting devices by role and vendor
drivenets_pcrs = topology_manager.get_devices(
    roles=[Roles.PCR],
    vendors=[Vendors.DRIVENETS],
)

# example of sending a command and deciphering the output
cli_session = device_manager.cli_sessions[device_name]
bgp_route = cli_session.send_command(
            command=f"show bgp route {prefix}",
            decipher=ShowBgpRouteDecipher,
        )


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