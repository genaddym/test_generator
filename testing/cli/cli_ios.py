# pragma: exclude file
"""Cisco IOS CLI Implementation

This module provides CLI session management for Cisco IOS devices.
Implements extensive error pattern matching, configuration management,
and vendor-specific command execution.

Available Classes:
    :py:class:`~orbital.testing.cli.cli_ios.CliIos`: Cisco IOS CLI implementation
"""

import re
import threading

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

terminal_stderr_re = [
    re.compile(r"% ?Error"),
    re.compile(r"ERROR:", re.IGNORECASE),
    re.compile(r"% ?Bad secret"),
    re.compile(r"[\r\n%] Bad passwords"),
    re.compile(r"invalid input", re.I),
    re.compile(r"(?:incomplete|ambiguous) command", re.I),
    re.compile(r"connection timed out", re.I),
    re.compile(r"[^\r\n]+ not found"),
    re.compile(r"'[^']' +returned error code: ?\d+"),
    re.compile(r"Bad mask", re.I),
    re.compile(r"% ?(\S+) ?overlaps with ?(\S+)", re.I),
    re.compile(r"% ?(\S+) ?Error: ?[\s]+", re.I),
    re.compile(r"% ?(\S+) ?Informational: ?[\s]+", re.I),
    re.compile(r"Command authorization failed"),
    re.compile(r"Command Rejected: ?[\s]+", re.I),
    re.compile(
        r"% General session commands not allowed under the address family",
        re.I,
    ),
    re.compile(r"% BGP: Error initializing topology", re.I),
    re.compile(r"%SNMP agent not enabled", re.I),
    re.compile(r"% Invalid", re.I),
    re.compile(
        r"%You must disable VTPv1 and VTPv2 or switch to VTPv3 "
        r"before configuring a VLAN name longer than 32 characters",
        re.I,
    ),
]

QUIT_KEYWORD = "quit"
EXIT_KEYWORD = "exit"
END_KEYWORD = "end"
CONFIGURE_KEYWORD = "configure terminal"
DISCARD_CANDIDATE = "abort"
COMMIT_KEYWORD = "commit"
COMMIT_CONFIRM_KEYWORD = "commit confirmed minutes %d"


DIFF_COMMAND = "show commit changes diff"
REPLACE_KEYWORD = "replace"
ROLLBACK_KEYWORD = "rollback configuration"
ROLLBACK_SUCCEEDED = "Configuration successfully rolled back"

DISABLE_PAGINATION_KEYWORD = "terminal length 0"

# additional time to wait after commit rollback to be safe. in seconds
COMMIT_EXTRA_TIME = 1

AWAITING_FOR_CONFIRM = "Awaiting for commit confirm"

logger = common.get_logger(__file__)


class CliIos(CliSession):
    """Cisco IOS CLI session management.

    Implements CLI session management for Cisco IOS devices.
    Handles vendor-specific command execution, configuration management,
    and session operations with extensive error pattern matching.

    Class parameters:
        :param hostname: Device hostname or IP address
        :type hostname: str
        :param username: Authentication username
        :type username: str
        :param password: Authentication password
        :type password: str

    Methods:
        _validate_output(output):
            Validates command output against error patterns.

        disable_pagination_cmd:
            Returns **terminal length 0** command for pagination control.

        close_session():
            Gracefully closes session using **quit** command.

        edit_config(candidate, replace=False, diff=False, confirm_timeout=None,
                   stop_on_error=True):
            Loads configuration in configure terminal mode.
            Supports commit confirmation with timeout.
            Shows diffs using **show commit changes diff**.

        _on_commit_timeout():
            Handles automatic rollback on commit confirmation timeout.

        execute_request_command(command):
            Handles interactive commands with yes/confirm prompts.

        confirm_commit():
            Confirms pending configuration changes.

        rollback(index):
            Rolls back to specific configuration version.
    """

    def __init__(self, hostname, username, password):
        super().__init__(
            hostname,
            username,
            password,
            Vendors.CISCO,
            session_conf={"look_for_keys": False, "allow_agent": False},
        )
        self.commit_confirm_timer = None
        self.awaiting_commit_confirm = False

    def _validate_output(self, output) -> bool:
        for regex in terminal_stderr_re:
            if regex.search(output):
                return False
        return True

    @property
    def disable_pagination_cmd(self) -> str:
        return DISABLE_PAGINATION_KEYWORD

    def close_session(self):
        try:
            if self.is_connected and not self.awaiting_commit_confirm:
                self.ssh.execute_shell_command(
                    QUIT_KEYWORD, wait_for_answer=False, reconnect=False
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

        if self.awaiting_commit_confirm:
            raise CommandFailed(AWAITING_FOR_CONFIRM)

        try:
            res = self.ssh.execute_shell_command(
                CONFIGURE_KEYWORD, shows_output=True
            )
            if not self._validate_output(res):
                raise UnexpectedOutput(res)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.error(f"Failed to enter configure mode: {ex}")
            raise ex

        for command in candidate.split("\n"):
            cmd = command.strip()
            if not cmd:
                continue
            logger.info(f"Executing command: {cmd}")
            try:
                self.ssh.execute_shell_command(cmd, shows_output=False)
            except (CommandFailed, UnexpectedOutput) as ex:
                logger.exception(ex)
                if not stop_on_error:
                    continue
                logger.warning(
                    "An error occurred while applying the configuration. Aborting configuration"
                )
                self.ssh.execute_shell_command(
                    DISCARD_CANDIDATE, shows_output=False
                )
                raise ex

        try:
            if diff:
                changes = self.ssh.execute_shell_command(
                    DIFF_COMMAND, shows_output=True
                )
            commit_cmd = COMMIT_KEYWORD
            if replace:
                commit_cmd = f"{COMMIT_KEYWORD} {REPLACE_KEYWORD}"
            if confirm_timeout:
                commit_cmd = COMMIT_CONFIRM_KEYWORD % confirm_timeout
            logger.info(f"Executing '{commit_cmd}'...")
            res = self.ssh.execute_shell_command(commit_cmd, shows_output=True)
            if not self._validate_output(res):
                logger.error(f"Commit failed: {res}")
                logger.info("Aborting changes...")
                self.ssh.execute_shell_command(
                    DISCARD_CANDIDATE, shows_output=False
                )
                raise CommitFailedException(res)
            logger.info("COMMIT succeeded")

            if confirm_timeout:
                self.awaiting_commit_confirm = True
                self.commit_confirm_timer = threading.Timer(
                    int(confirm_timeout) * 60 + COMMIT_EXTRA_TIME,
                    self._on_commit_timeout,
                )
                self.commit_confirm_timer.start()
            else:
                self.ssh.execute_shell_command(END_KEYWORD, shows_output=False)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.error(
                f"An error occurred while applying configuration: {ex}"
            )
            raise ex
        return changes

    def _on_commit_timeout(self):
        logger.info(
            "Commit was not confirmed. Configuration rolled back to the previous"
            " configuration\nExiting configuration mode..."
        )
        try:
            self.ssh.execute_shell_command(END_KEYWORD, shows_output=False)
            self.awaiting_commit_confirm = False
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.error(
                f"An error occurred while exiting configuration mode: {ex}"
            )
            raise ex

    def execute_request_command(self, command: str):
        if self.awaiting_commit_confirm:
            raise CommandFailed(AWAITING_FOR_CONFIRM)

        self.ssh.execute_shell_command(
            command,
            match_reg=r".*\[(confirm|yes|no|cancel)\]",
            shows_output=True,
        )
        self.ssh.execute_shell_command("y", shows_output=True)

    def confirm_commit(self, session_name=None) -> None:
        if not self.awaiting_commit_confirm:
            raise CommandFailed("There is no commit awaiting for confirmation")
        self.awaiting_commit_confirm = False
        self.commit_confirm_timer.cancel()
        try:
            logger.info(f"Executing '{COMMIT_KEYWORD}'...")
            res = self.ssh.execute_shell_command(
                COMMIT_KEYWORD, shows_output=True
            )
            if not self._validate_output(res):
                logger.error(f"Commit failed: {res}")
                raise CommitFailedException(res)
            self.ssh.execute_shell_command(END_KEYWORD, shows_output=False)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.exception(ex)
            raise ex

    def rollback(self, index) -> None:
        if self.awaiting_commit_confirm:
            raise CommandFailed(AWAITING_FOR_CONFIRM)

        try:
            cmd = f"{ROLLBACK_KEYWORD} {index}"
            logger.info(f"Executing '{cmd}'...")
            res = self.ssh.execute_shell_command(cmd, shows_output=True)
            if ROLLBACK_SUCCEEDED not in res:
                logger.error(f"Rollback failed: {res}")
                raise UnknownCliException(res)
        except (CommandFailed, UnexpectedOutput) as ex:
            logger.exception(ex)
            raise ex
