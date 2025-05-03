"""
Pytest fixtures available in all Orbital/IDAN network functionality tests.
"""

import pathlib

import pytest
from orbital.testing.device_manager import DeviceManager
from orbital.testing.inventory_manager import InventoryManager
from orbital.testing.topology.topology_manager import TopologyManager

DEVICE_CONFIG = "device_config"
TOPOLOGY_CONFIG = "topology_config"


@pytest.fixture(autouse=True, scope="session")
def get_root_dir_fixture() -> pathlib.Path:
    """Get the root directory of the test suite.
    
    This fixture is required for maintaining file paths across different test environments.
    It eliminates the need for hardcoded absolute paths.

    :return: Path object pointing to the directory containing the test files
    """
    return pathlib.Path(__file__).parent


@pytest.fixture(scope="class")
def device_config(get_root_dir_fixture: pathlib.Path, request) -> str:
    """Load the device configuration file path.

    :param get_root_dir_fixture: Root directory of test suite
    :type get_root_dir_fixture: pathlib.Path
    :param request: Pytest request object containing the parametrized value
    :type request: pytest.FixtureRequest
    
    :return: Absolute path to the device configuration file
    :rtype: str
    """
    return str((get_root_dir_fixture / request.param).absolute())


@pytest.fixture(scope="class")
def inventory_manager(device_config) -> InventoryManager:
    """Create and initialize the inventory manager with device configuration.

    :param device_config: Path to the device configuration file
    :type device_config: str
    
    :return: Initialized inventory manager instance
    """
    _inventory = InventoryManager()
    _inventory.load(device_config)
    return _inventory


@pytest.fixture()
def device_manager(inventory_manager: InventoryManager, scope: str = "class") -> DeviceManager:
    """Create and initialize the device manager with inventory devices.

    :param inventory_manager: Initialized inventory manager containing device info
    :param scope: Scope of the fixture, defaults to "class"

    :return: Initialized device manager instance
    """
    m = DeviceManager()
    m.init_devices(inventory_manager.devices)
    return m


@pytest.fixture(scope="class")
def topology_config(get_root_dir_fixture: pathlib.Path, request: pytest.FixtureRequest) -> str:
    """Load the topology configuration file path.

    :param get_root_dir_fixture: Root directory of test suite
    :param request: Pytest request object containing the parametrized value

    :return: Absolute path to the topology configuration file
    """
    return (get_root_dir_fixture / request.param).as_posix()


@pytest.fixture(scope="class")
def topology_manager(topology_config: str) -> TopologyManager:
    """Create and initialize the topology manager with configuration.

    :param topology_config: Path to the topology configuration file

    :return: Initialized topology manager instance
    """
    manager = TopologyManager()
    manager.load(topology_config)
    return manager
