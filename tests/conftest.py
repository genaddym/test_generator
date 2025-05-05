"""
Pytest fixtures available in all Orbital/IDAN network functionality tests.
"""

import pathlib
import pytest



@pytest.fixture(autouse=True, scope="session")
def get_root_dir_fixture() -> pathlib.Path:
    """Get the root directory of the test suite.
    
    This fixture is required for maintaining file paths across different test environments.
    It eliminates the need for hardcoded absolute paths.

    :return: Path object pointing to the directory containing the test files
    """
    return pathlib.Path(__file__).parent
