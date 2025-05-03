# pragma: exclude file
"""
This module defines the DeviceManager class used for managing network devices.
"""

from orbital import common
from orbital.testing.device import Device
from orbital.testing.cli.cli_ios import CliIos
from orbital.testing.cli.cli_ceos import CliCeos
from orbital.testing.cli.cli_dnos import CliDnos
from orbital.testing.otg_client.otg_api_client import OtgApiClient
from orbital.testing.common.general.python_helpers import Singleton

logger = common.get_logger(__file__)


class DeviceManager(metaclass=Singleton):
    """
    A class to manage network devices.

    Attributes:
    cli_sessions : dict
        A dictionary to store CLI sessions for devices.
    otg_devices : dict
        A dictionary to store OTG API clients for devices.
    """

    def __init__(self):
        """
        Initializes the DeviceManager with empty dictionaries for CLI sessions and OTG devices.
        """
        self.cli_sessions = {}
        self.otg_devices = {}

    def init_devices(self, devices: dict[str, Device]) -> None:
        """
        Initializes devices based on their vendor and stores the corresponding CLI
        sessions or OTG API clients.

        Parameters:
        devices (dict[str, Device]): A dictionary of device names and Device objects.
        """
        self.cli_sessions = {}
        self.otg_devices = {}
        for device_name, device in devices.items():
            if not device.vendor:
                raise ValueError(
                    f"Device vendor is mandatory for device {device.hostname}"
                )
            if device.vendor.lower() == "drivenets":
                self.cli_sessions[device_name] = CliDnos(
                    device.hostname, device.username, device.password
                )
            elif device.vendor.lower() == "arista":
                self.cli_sessions[device_name] = CliCeos(
                    device.hostname, device.username, device.password
                )
            elif device.vendor.lower() == "cisco":
                self.cli_sessions[device_name] = CliIos(
                    device.hostname, device.username, device.password
                )
            elif device.vendor.lower() == "ixia":
                self.otg_devices[device_name] = OtgApiClient(
                    name=device_name,
                    base_url=f"https://{device.hostname}",
                    port=int(device.port),
                )
            else:
                raise ValueError(
                    f"Unsupported vendor '{device.vendor}' for device {device_name}"
                )
