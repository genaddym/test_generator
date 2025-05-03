# pragma: exclude file
"""DriveNets OS CLI Implementation

This module provides CLI session management for DriveNets OS devices.
Implements configuration management, commit/rollback operations,
and vendor-specific command execution.

Available Classes:
    :py:class:`~orbital.testing.cli.cli_dnos.CliDnos`: DriveNets OS CLI implementation
"""

from orbital import common
from orbital.testing.common.vendors import Vendors
from orbital.testing.cli.cli_session import CliSession
from orbital.testing.common.exceptions import (
    CommandFailed,
    SessionClosed,
    UnexpectedOutput,
    UnknownCliException,
    CommitFailedException,
)

QUIT_KEYWORD = "quit"
EXIT_KEYWORD = "exit"
TOP_KEYWORD = "top"
CONFIGURE_KEYWORD = "configure"
DISCARD_CANDIDATE = "rollback 0"
COMMIT_KEYWORD = "commit"
COMMIT_CONFIRM_KEYWORD = "commit confirm"
COMMIT_AND_EXIT_KEYWORD = "commit and-exit"
DIFF_COMMAND = "show config compare rollback 0 rollback 1"
COMMIT_SUCCEEDED = "Commit succeeded"
COMMIT_CONFIRMED = "Commit confirmed"
ROLLBACK_COMPLETE = "rollback complete"
LOAD_OVERRIDE_COMMAND = "load override factory-default"
ROLLBACK_KEYWORD = "rollback"


logger = common.get_logger(__file__)


class CliDnos(CliSession):
    """DriveNets OS CLI session management.

    Implements CLI session management for DriveNets OS devices.
    Handles vendor-specific command execution, configuration management,
    and session operations.

    Class parameters:
        :param hostname: Device hostname or IP address
        :type hostname: str
        :param username: Authentication username
        :type username: str
        :param password: Authentication password
        :type password: str

    Methods:
        disable_pagination_suffix:
            Returns **|no-more** suffix for pagination control.

        close_session():
            Gracefully closes session using **quit** command.

        edit_config(candidate, replace=False, diff=False, confirm_timeout=None,
                   stop_on_error=True):
            Loads configuration in configure mode.
            Supports factory defaults with **load override factory-default**.
            Shows diffs using **show config compare rollback 0 rollback 1**.

        execute_request_command(command):
            Handles interactive commands with yes/no prompts.

        confirm_commit():
            Confirms pending configuration changes.

        _commit():
            Internal method for committing configuration.

        rollback(index):
            Rolls back to specific configuration version.
    """

    def __init__(self, hostname, username, password):
        super().__init__(hostname, username, password, Vendors.DRIVENETS)

    @property
    def disable_pagination_suffix(self) -> str:
        return "|no-more"

    def close_session(self):
        try:
            if self.is_connected is True:
                (
                    self.ssh.execute_shell_command(
                        QUIT_KEYWORD, wait_for_answer=False, reconnect=False
                    )
                )
        except (CommandFailed, OSError, SessionClosed):
            pass
        finally:
            self.ssh.close()

    def edit_config(
        self,
        candidate,
        replace=False,
        diff=False,
        confirm_timeout=None,
        session_name=None,
        stop_on_error=True,
    ) -> str:
        changes = None

        try:
            self.ssh.execute_shell_command(
                CONFIGURE_KEYWORD, shows_output=False
            )
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.error(f"Failed to enter configure mode: {ex}")
            raise ex

        if replace:
            try:
                self.ssh.execute_shell_command(
                    LOAD_OVERRIDE_COMMAND, shows_output=False
                )
            except (CommandFailed, UnexpectedOutput) as ex:
                logger.error(f"Failed to override factory defaults: {ex}")
                raise ex

        for command in candidate.split("\n"):
            cmd = command.strip()
            if not cmd:
                continue
            logger.debug(f"Executing command: {cmd}")
            try:
                self.ssh.execute_shell_command(cmd, shows_output=False)
            except (CommandFailed, UnexpectedOutput) as ex:
                logger.exception(ex)
                if not stop_on_error:
                    continue
                logger.warning(
                    "An error occurred while applying the configuration. "
                    "The candidate will be disregarded"
                )
                self.ssh.execute_shell_command(
                    DISCARD_CANDIDATE, shows_output=False
                )
                raise ex

        try:
            commit_cmd = COMMIT_AND_EXIT_KEYWORD
            if confirm_timeout:
                commit_cmd = f"{COMMIT_CONFIRM_KEYWORD} {confirm_timeout}"
            logger.debug(f"Executing '{commit_cmd}'...")
            res = self.ssh.execute_shell_command(commit_cmd, shows_output=True)
            if COMMIT_SUCCEEDED not in res:
                logger.error(f"Commit failed: {res}")
                logger.debug("Trying to discard changes...")
                self.ssh.execute_shell_command(
                    DISCARD_CANDIDATE, shows_output=False
                )
                raise CommitFailedException(res)
            logger.debug("COMMIT succeeded")
            if diff:
                changes = self.ssh.execute_shell_command(
                    DIFF_COMMAND, shows_output=True
                )
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.error(
                f"An error occurred while applying configuration: {ex}"
            )
            raise ex
        return changes

    def execute_request_command(self, command: str):
        self.ssh.execute_shell_command(
            command, match="(yes/no) [no]?", shows_output=False
        )
        self.ssh.execute_shell_command("yes")

    def confirm_commit(self, session_name=None) -> None:
        try:
            logger.debug("Entering configure mode...")
            self.ssh.execute_shell_command(
                CONFIGURE_KEYWORD, shows_output=False
            )
            logger.debug(f"Executing '{COMMIT_AND_EXIT_KEYWORD}'...")
            res = self.ssh.execute_shell_command(
                COMMIT_AND_EXIT_KEYWORD, shows_output=True
            )
            if COMMIT_SUCCEEDED not in res and COMMIT_CONFIRMED not in res:
                logger.error(f"Commit failed: {res}")
                raise CommitFailedException(res)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.exception(ex)
            raise ex

    def _commit(self) -> None:
        try:
            logger.debug(f"Executing '{COMMIT_AND_EXIT_KEYWORD}'...")
            res = self.ssh.execute_shell_command(
                COMMIT_AND_EXIT_KEYWORD, shows_output=True
            )
            if COMMIT_SUCCEEDED not in res:
                logger.error(f"Commit failed: {res}")
                raise CommitFailedException(res)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.exception(ex)
            raise ex

    def rollback(self, index) -> None:
        try:
            self.ssh.execute_shell_command(
                CONFIGURE_KEYWORD, shows_output=False
            )
            cmd = f"{ROLLBACK_KEYWORD} {index}"
            logger.debug(f"Executing '{cmd}'...")
            res = self.ssh.execute_shell_command(cmd, shows_output=True)
            if ROLLBACK_COMPLETE not in res:
                logger.error(f"Rollback failed: {res}")
                raise UnknownCliException(res)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.exception(ex)
            raise ex
        self._commit()
