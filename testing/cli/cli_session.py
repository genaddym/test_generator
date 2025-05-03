# pragma: exclude file
"""CLI Session Base Class

This module provides the base interface for CLI session management across different
network device vendors. It defines common operations for configuration management
and command execution.

Example:
    Basic usage pattern for vendor implementations::

        class VendorCli(CliSession):
            def __init__(self, hostname, username, password):
                super().__init__(hostname, username, password)

            def edit_config(self, candidate, replace=False):
                # Vendor-specific implementation
                pass
"""

from abc import ABC, abstractmethod

from orbital.testing.ssh_client.ssh_client import SSHClient
from orbital.testing.helpers.deciphers.decipher_base import Decipher
from orbital.testing.helpers.show_cmd_handlers.show_cmd_types import (
    ShowCommandType,
)
from orbital.testing.helpers.show_cmd_handlers.show_cmd_handler import (
    ShowCmdHandlerRegistry,
)

SHOW_COMMAND_PREFIX = "show "


class CliSession(ABC):
    """
    Base class for CLI session management.

    Provides interface and basic implementation for managing CLI sessions
    with network devices. Handles connection lifecycle, command execution,
    and configuration management.

    Class parameters:
        :param hostname: Device hostname or IP address
        :type hostname: str
        :param username: Authentication username
        :type username: str
        :param password: Authentication password
        :type password: str
        :param session_conf: Additional session configuration
        :type session_conf: dict, optional

    Methods:
        open_session():
            Opens a new CLI session with the device.
            Establishes SSH connection and waits for device prompt.
            Raises SessionClosed when connection cannot be established.
            Raises UnexpectedOutput when prompt is not detected.

        close_session():
            Gracefully closes the CLI session with a clear exit message.
            Vendor-specific implementation required.
            Raises CommandFailed when exit command fails.
            Raises SessionClosed when session is already closed.

        disconnect():
            Force disconnects the SSH session without graceful exit.

        edit_config(candidate, replace=False, diff=False, confirm_timeout=None,
                   session_name=None, stop_on_error=True):
            Loads candidate configuration into the network device.
            Args:
                candidate: Configuration to load
                replace: True to replace config, False to merge
                diff: Generate diff of changes
                confirm_timeout: Minutes before automatic rollback
                session_name: Configuration session name
                stop_on_error: Stop on error or continue
            Returns diff of changes if diff=True.
            Raises UnknownCliException, CommandFailed, SessionClosed,
                  UnexpectedOutput, CommitFailedException.

        send_command(command, sendonly=False, decipher=None):
            Executes command over device connection.
            For show commands, handles pagination if supported.
            Args:
                command: Command to send
                sendonly: Send without waiting for response
                decipher: Optional response processor
            Returns command output or processed result.
            Raises CommandFailed, UnexpectedOutput, SessionClosed.

        confirm_commit(session_name=None):
            Confirms pending configuration changes.
            Vendor-specific operation for confirming changes.
            Args:
                session_name: Optional configuration session
            Raises CommandFailed, UnexpectedOutput, CommitFailedException.

        rollback(index):
            Rolls back configuration to previous state.
            Vendor-specific operation for configuration rollback.
            Args:
                index: Configuration history index
            Raises CommandFailed, UnexpectedOutput, UnknownCliException.
    """

    def __init__(
        self, hostname, username, password, vendor, session_conf=None
    ):
        """Initialize CLI session with device credentials.

        Args:
            hostname: Device hostname or IP address
            username: Authentication username
            password: Authentication password
            session_conf: Additional session configuration, defaults to None
        """
        self.ssh = SSHClient(
            hostname=hostname,
            username=username,
            password=password,
            session_conf=session_conf if session_conf else {},
        )
        self._pagination_disabled = False
        self.vendor = vendor

    def open_session(self):
        """Opens a new CLI session with the device.

        Establishes SSH connection and waits for device prompt.
        Raises SessionClosed when connection cannot be established.
        Raises UnexpectedOutput when prompt is not detected.
        """
        self.ssh.connect_wait_for_prompt(prompt_retries=3)

    @abstractmethod
    def close_session(self):
        """Gracefully closes the CLI session with a clear exit message.

        Vendor-specific implementation required.
        Raises CommandFailed when exit command fails.
        Raises SessionClosed when session is already closed.
        """

    def disconnect(self):
        """Force disconnects the SSH session without graceful exit."""
        self.ssh.close()

    @property
    def is_connected(self):
        """Checks if the SSH session is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.ssh.is_connected

    @property
    def disable_pagination_cmd(self) -> str:
        """Command to disable pagination on the device.

        Returns:
            str: The command string to disable pagination.
        """
        return ""

    @property
    def disable_pagination_suffix(self) -> str:
        """Suffix to append to commands to disable pagination.

        Returns:
            str: The suffix string to disable pagination.
        """
        return ""

    @abstractmethod
    def execute_request_command(self, command: str):
        """Executes a request command on the device.

        Args:
            command (str): The command to execute.
        """

    @abstractmethod
    def edit_config(
        self,
        candidate,
        replace=False,
        diff=False,
        confirm_timeout=None,
        session_name=None,
        stop_on_error=True,
    ) -> str:
        """Loads candidate configuration into the network device.

        Args:
            candidate: Configuration to load.
            replace (bool): True to replace config, False to merge.
            diff (bool): Generate diff of changes.
            confirm_timeout: Minutes before automatic rollback.
            session_name: Configuration session name.
            stop_on_error (bool): Stop on error or continue.

        Returns:
            str: Diff of changes if diff=True.

        Raises:
            UnknownCliException, CommandFailed, SessionClosed, UnexpectedOutput,
            CommitFailedException.
        """

    def send_command(
        self, command: str, sendonly: bool = False, decipher: Decipher = None
    ):
        """Executes command over device connection.

        For show commands, handles pagination if supported.

        Args:
            command (str): Command to send.
            sendonly (bool): Send without waiting for response.
            decipher (Decipher): Optional response processor.

        Returns:
            str: Command output or processed result.

        Raises:
            CommandFailed, UnexpectedOutput, SessionClosed.
        """
        if not command:
            return None

        if (
            not self._pagination_disabled
            and self.disable_pagination_cmd
            and command.startswith(SHOW_COMMAND_PREFIX)
        ):
            self.ssh.execute_shell_command(
                self.disable_pagination_cmd,
                wait_for_answer=True,
                shows_output=True,
            )
            self._pagination_disabled = True

        if self.disable_pagination_suffix and command.startswith(
            SHOW_COMMAND_PREFIX
        ):
            command = f"{command}{self.disable_pagination_suffix}"

        cli_output = self.ssh.execute_shell_command(
            command, wait_for_answer=not sendonly, shows_output=not sendonly
        )
        if decipher:
            return decipher.decipher(cli_output)
        return cli_output

    @abstractmethod
    def confirm_commit(self, session_name=None) -> None:
        """Confirms pending configuration changes.

        Vendor-specific operation for confirming changes.

        Args:
            session_name: Optional configuration session.

        Raises:
            CommandFailed, UnexpectedOutput, CommitFailedException.
        """

    @abstractmethod
    def rollback(self, index) -> None:
        """Rolls back configuration to previous state.

        Vendor-specific operation for configuration rollback.

        Args:
            index: Configuration history index.

        Raises:
            CommandFailed, UnexpectedOutput, UnknownCliException.
        """

    def send_show_command(self, command_type: ShowCommandType, **kwargs):
        """Executes a show command over the device connection.

        The method will find a specific command syntax and decipher for the command type
        according to the vendor.

        Args:
            command_type (ShowCommandType): The type of the show command to execute.
            kwargs: The arguments to pass to the command.

        Returns:
            str: The output of the show command.
        """
        return ShowCmdHandlerRegistry.get_handler(
            command_type, self.vendor.value
        ).execute(self, **kwargs)
