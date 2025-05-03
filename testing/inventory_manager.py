# pragma: exclude file
"""
The devices in the configuration file are a list consisting of Device instance representations
inventory yml example:

devices:
  tcr03:
    hostname: 100.93.118.28
    username: dnroot
    password: dnroot
    vendor: drivenets
  tcr04:
    hostname: 100.93.118.29
    username: dnroot
    password: dnroot
    vendor: drivenets
"""

from dataclasses import field, dataclass

import yaml

from orbital import common
from orbital.testing.device import Device
from orbital.testing.common.general.python_helpers import Singleton

logger = common.get_logger(__file__)


@dataclass
class InventoryManager(metaclass=Singleton):
    """
    A class to manage the inventory of network devices.

    Attributes:
    devices : dict
        A dictionary to store Device instances.
    """

    devices: dict[str, Device] = field(default_factory=dict)

    def load(self, file_path):
        """
        Load inventory object from yaml file.

        Parameters:
        file_path (str): The path to the yaml file.
        """
        try:
            with open(file_path) as f:
                yaml_data = yaml.safe_load(f)
            for key, config in yaml_data.items():
                if key == "devices":
                    for device_name in config:
                        self.devices[device_name] = Device(
                            **config[device_name]
                        )
        except yaml.YAMLError as e:
            logger.error(f"Error parsing inventory: {e}")
            raise
        except FileNotFoundError as e:
            logger.error(f"Error loading inventory: {e}")
            raise

    def add_device(self, device: Device) -> None:
        """Add a device to the inventory.

        Args:
            device: The device to add.
        """
        if device.id in self.devices:
            logger.warning(
                "Device with ID %s already exists in inventory", device.id
            )
            return

        logger.info("Adding device %s to inventory", device.id)
        self.devices[device.id] = device
