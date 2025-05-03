"""CLI Session Management Package

This package provides interfaces and implementations for managing CLI sessions
with network devices from different vendors. It handles connection management,
command execution, and configuration changes.

Available Classes:
    :py:class:`~orbital.testing.cli.cli_session.CliSession`: Base CLI session interface
    :py:class:`~orbital.testing.cli.cli_ceos.CliCeos`: Arista CEOS CLI implementation
    :py:class:`~orbital.testing.cli.cli_ios.CliIos`: Cisco IOS CLI implementation
    :py:class:`~orbital.testing.cli.cli_dnos.CliDnos`: DriveNets OS CLI implementation
"""

from orbital.testing.cli.cli_ios import CliIos
from orbital.testing.cli.cli_ceos import CliCeos
from orbital.testing.cli.cli_dnos import CliDnos
from orbital.testing.cli.cli_session import CliSession

__all__ = ["CliSession", "CliCeos", "CliIos", "CliDnos"]
