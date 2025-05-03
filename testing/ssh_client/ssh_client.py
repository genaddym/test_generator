# pragma: exclude file
"""
SSH Client
~~~~~~~~~~

Description:
    |A simple SSH client that can perform non blocking cli operations on a remote host
    |via SSH connection.

"""

import re
import socket
import logging
import warnings
from time import sleep, monotonic
from datetime import datetime, timedelta

import scp
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
import paramiko

import orbital.common as common
from orbital.testing.common import exceptions
from orbital.testing.common.decorators import (
    inspections as inspections_decorators,
)
from orbital.testing.common.general.inspections import get_args_values
from orbital.testing.common.general.validations import return_as_list

from . import consts

logger = common.get_logger(__file__)

# disable paramiko logger
logging.getLogger("paramiko").setLevel(100)

paramiko.Transport._preferred_ciphers = (
    "aes128-ctr",
    "aes128-cbc",
    "blowfish-cbc",
    "3des-cbc",
)


class SSHClient:
    PROMPT_REGEX = r".*?{cmd}\n?(.*)(\s.*[$#>] ?)$"
    ADDITIONAL_CMD_FAILURES = ["Connection timed out", "Connection refused"]

    @inspections_decorators.discard_unknown_args
    def __init__(
        self,  # NOSONAR
        hostname=None,
        username=None,
        password=None,
        key_filename=None,
        port=22,
        connect_timeout=60,
        connect_retries=3,
        command_timeout=600,
        command_retry=True,
        prompt=None,
        width=1500,
        height=1000,
        cmd_failures=(),
        prompt_retries=3,
        prompt_match=consts.DEFAULT_DEVICE_PROMPT_REGEX,
        session_conf=None,
        **kwargs,
    ):
        self.log_prefix = f"S-<{str(id(self))[-5:]}> "
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.connect_timeout = connect_timeout
        self.connect_retries = connect_retries
        self.command_timeout = command_timeout
        self.command_retry = command_retry
        self._prompt = prompt
        self.width = width
        self.height = height
        self.cmd_failures = cmd_failures
        self.prompt_retries = prompt_retries

        # the prompt we expect during open session
        self.prompt_match = prompt_match

        self._session = None
        self.shell = None

        if (
            self.username is None
            or (self.password is None and self.key_filename is None)
            or self.hostname is None
        ):
            message = "provided username: {} (password: {} or key_filename: {}) host: {} - one is missing, expecting all three".format(
                self.username, self.password, self.key_filename, self.hostname
            )
            logger.error(self.log_prefix + message)
            raise exceptions.ConnectionFail(message)

        self.session_conf = session_conf

    @property
    def prompt(self):
        if self._prompt is None:
            self._prompt = self.PROMPT_REGEX

        return self._prompt

    @prompt.setter
    def prompt(self, prompt):
        logger.debug(f"Set prompt of ssh session be {prompt}")
        self._prompt = prompt

    def connect_wait_for_prompt(self, prompt_retries):
        last_exception = None
        for i in range(prompt_retries):
            try:
                logger.debug(
                    self.log_prefix
                    + f"waiting for prompt, retry number {i + 1}, out of {prompt_retries}"
                )
                self.open_session()
                self._wait_for_prompt()
                break
            except exceptions.MainException as e:
                last_exception = e
                logger.error(self.log_prefix + str(e))
                self.close()
        else:
            if last_exception:
                raise last_exception

    @property
    def session(self):
        if not self._session:
            self.connect_wait_for_prompt(self.prompt_retries)
        return self._session

    def open_session(self):
        """
        currently only connecting with username and password is supported
        added support for connecting with username and public key
        raises ConnectionFail
        """
        self._session = paramiko.SSHClient()

        # since we're in a lab environment, we can assume we're about to connect only to machines you trust
        self._session.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # check first connection with public key
        if self.key_filename is not None:
            logger.debug(
                self.log_prefix
                + "Opening SSH session. host: {}, port: {}, username: {}, key_filename: {}".format(
                    self.hostname, self.port, self.username, self.key_filename
                )
            )
        else:
            logger.debug(
                self.log_prefix
                + "Opening SSH session. host: {}, port: {}, username: {}, password: *****".format(
                    self.hostname, self.port, self.username
                )
            )
        try:
            # check first connection with public key
            if self.key_filename is not None:
                self._session.connect(
                    self.hostname,
                    username=self.username,
                    port=self.port,
                    key_filename=self.key_filename,
                    timeout=self.connect_timeout,
                    **self.session_conf,
                )
            else:
                self._session.connect(
                    self.hostname,
                    username=self.username,
                    port=self.port,
                    password=self.password,
                    timeout=self.connect_timeout,
                    **self.session_conf,
                )
            # https://github.com/paramiko/paramiko/issues/175
            self._session._transport.window_size = 2147483647
        except paramiko.ssh_exception.BadHostKeyException:
            message = "host key could not be verified"
            logger.error(self.log_prefix + message)
            raise exceptions.BadCredentials(message)
        except paramiko.ssh_exception.AuthenticationException:
            if self.key_filename is not None:
                message = f"authentication failed. wrong credentials: {self.username} - {self.key_filename}"
            else:
                message = f"authentication failed. wrong credentials: {self.username} - {self.password}"
            logger.error(self.log_prefix + message)
            # if the session is open - close it
            if self._session:
                self.close()
            raise exceptions.BadCredentials(message)
        except (paramiko.ssh_exception.SSHException, OSError) as e:
            message = f"could not establish connection, an error occurred: {e}"
            logger.error(self.log_prefix + message)
            raise exceptions.ConnectionFail(message)
        except TimeoutError:  # NOSONAR
            message = "could not establish connection, time's out!"
            logger.error(self.log_prefix + message)
            raise exceptions.ConnectionFail(message)

        try:
            self.shell = self._session.invoke_shell(
                width=self.width, height=self.height
            )
        except paramiko.SSHException as e:
            logger.error(
                self.log_prefix
                + f"could not invoke ssh shell, exception raised: '{e}'"
            )

        if self.key_filename is not None:
            logger.debug(
                self.log_prefix
                + "SSH session is open. host: {}, port: {}, username: {}, key_filename: {}".format(
                    self.hostname, self.port, self.username, self.key_filename
                )
            )
        else:
            logger.debug(
                self.log_prefix
                + "SSH session is open. host: {}, port: {}, username: {}, password: *****".format(
                    self.hostname, self.port, self.username
                )
            )

    def _wait_for_prompt(self):
        prompt_match = self.prompt_match
        try:
            logger.debug(
                self.log_prefix
                + f"waiting {self.connect_timeout} sec to receive prompt..."
            )
            output = self._read_until_match(
                self.shell,
                monotonic() + self.connect_timeout,
                match=prompt_match,
            )
            logger.debug(
                self.log_prefix
                + f"Received SSH user prompt, output:\n{output}"
            )
            return output
        except exceptions.ExecutionTimeout as e:
            try:
                # Connection to <DESTINATION> closed.
                self.shell.send("\n")
            except OSError as e:
                logger.warning(
                    f"Connection closed immediately after connected: {e}."
                )
                # because we fail on executing on open_session, switch excpetion to ConnectionFail
                raise exceptions.ConnectionFail(
                    "Connection closed by remote host"
                )
            raise exceptions.PromptException(e)

    def get_banner(self):
        """
        Gets SSH login banner message
        :return: str
        """
        banner = None
        if not self.session:
            t = paramiko.Transport((self.hostname, self.port))
            try:
                t.connect()
                t.auth_none("parmiko_banner_retrieval_service")
            except (
                paramiko.BadAuthenticationType
            ):  # Bad authentication is expected because no credentials were used
                banner = t.get_banner()
        else:
            banner = self.session.get_transport().get_banner()

        if banner:
            banner = banner.decode("utf-8", "ignore")

        return banner

    def __repr__(self):
        return "SSH Client"

    def close(self, close_transport=True):
        if self._session:
            if close_transport:
                # we have to close also the transport
                # otherwise we'll have dangling ssh connection to our machine
                transport = self._session.get_transport()
                if transport:
                    transport.close()
            self._session.close()
            logger.debug(
                self.log_prefix
                + f"SSH session (host: {self.hostname}) is closed"
            )
        self._session = None

    def is_connected(self):
        """
        Return status of the current SSH connection
        :return: boolean
        """
        transport = self._session.get_transport() if self._session else False
        return bool(transport and transport.is_active())

    @property
    def session_address(self):
        """
        :return: a tuple of ip and port of the session
        """
        if not self.is_connected():
            raise exceptions.SessionClosed

        return self.session.get_transport().sock.getsockname()

    def execute_command(self, command, timeout=0, wait_for_answer=True):
        """
        Execute a blocking command at the router OS
        :raises: ExecutionTimeout, ExecutionFailed
        """
        timeout = timeout if timeout else self.command_timeout
        channel = self.session.get_transport()

        if not self.is_connected() or not channel:
            message = f"could not execute '{command}', session is not open. reconnecting"
            logger.error(self.log_prefix + message)
            self.reconnect()

        channel = channel.open_session()
        channel.set_combine_stderr(True)
        channel.settimeout(timeout)
        logger.debug(f"executing '{command}'")
        try:
            channel.exec_command(command)
        except paramiko.ssh_exception.SSHException:
            message = f"could not execute '{command}'"
            logger.warning(self.log_prefix + message)
            channel.close()
            raise exceptions.ExecutionFailed(message)
        except TimeoutError:
            message = (
                f"timeout before reply to command '{command}' is received"
            )
            logger.warning(self.log_prefix + message)
            if not wait_for_answer:
                raise exceptions.ExecutionTimeout(message, None)

        if not wait_for_answer:
            channel.close()
            return

        # read what you got
        data = []

        # for command to exit
        raise_receive_timeout = False
        start_time = monotonic()
        while True:
            while channel.recv_ready():
                try:
                    data_buffer = channel.recv(consts.MAX_BUFFER).decode(
                        "utf-8", "ignore"
                    )
                    data.append(data_buffer)
                except TimeoutError as e:
                    logger.warning(
                        self.log_prefix
                        + f"exception raised during output retrieval of '{command}': '{e}'"
                    )
                    raise_receive_timeout = True
                    break

            if channel.exit_status_ready():
                break

            time_diff = monotonic() - start_time
            if time_diff > timeout:
                raise_receive_timeout = True
                logger.warning(
                    self.log_prefix
                    + "{:.2f} seconds passed, timeout exceeded while receiving output of '{}'".format(
                        time_diff, command
                    )
                )
                break

            sleep(0.0075)

        channel.close()
        output = "".join(data)

        if raise_receive_timeout:
            message = f"cannot get full output of '{command}'.output buffer has: '{output}'"
            logger.warning(self.log_prefix + message)
            raise exceptions.ExecutionTimeout(message, output)

        return output

    def scp_put(self, src, dst=".", recursive=False):
        """
        Performs scp put

        :param src: Source file.
        :type src: str

        :param dst: Destination path.
        :type dst: str

        :param recursive: Copy dir recursively, False by default.
        :type recursive: bool

        :raises: SCPException

        """
        logger.debug(
            f"executing 'scp put' to '{self.hostname}'. putting file '{src}' from local machine, to remote "
            f"destination '{dst}'"
        )
        scp_obj = scp.SCPClient(self.session.get_transport())
        try:
            scp_obj.put(src, remote_path=dst, recursive=recursive)
        except (scp.SCPException, OSError) as e:
            message = f"exception was raised during 'scp put' from '{src}' to '{dst}': '{e}'"
            logger.warning(self.log_prefix + message)
            raise exceptions.SCPException(message)
        finally:
            scp_obj.close()

    def scp_get(self, src, dst, recursive=False):
        logger.debug(
            f"executing 'scp get' from local machine. getting file '{src}' from '{self.hostname}', to local "
            f"destination '{dst}'"
        )
        scp_obj = scp.SCPClient(self.session.get_transport())
        try:
            scp_obj.get(src, local_path=dst, recursive=recursive)
        except (scp.SCPException, OSError) as e:
            message = f"exception was raised during 'scp get' from '{src}' to '{dst}': '{e}'"
            logger.warning(self.log_prefix + message)
            raise exceptions.SCPException(message)
        finally:
            scp_obj.close()

    def output_validation(
        self,
        output,
        command,
        shows_output=False,
        additional_cmd_failures=None,
        validate_output=True,
    ):
        if additional_cmd_failures is None:
            additional_cmd_failures = []
        else:
            additional_cmd_failures = return_as_list(additional_cmd_failures)

        # if a process was killed in background, clean output
        output = re.sub(
            r"\[\d+\].* (Exit|Killed|Terminated|Done) .*\n?", "", output
        )

        # In order to catch any commands failures,
        # we check the output only after we assure that output not should be empty
        if validate_output and shows_output is not False:

            for failure in tuple(self.cmd_failures) + tuple(
                additional_cmd_failures
            ):
                if failure in output:
                    message = (
                        f"Command '{command}'.\nfailed with error: '{output}'"
                    )
                    logger.error(self.log_prefix + message)
                    raise exceptions.CommandFailed(output)

        if (
            shows_output is None
        ):  # if shows_output is none, don't perform output validation
            return output

        if shows_output:
            if not output:
                message = (
                    f"{consts.NO_OUTPUT_EXCEPTION_MSG} for command '{command}'"
                )
                logger.debug(self.log_prefix + message)
                raise exceptions.UnexpectedOutput(message)
            return output

        if output:
            # if unexpected output found.
            message = (
                f"Command '{command}'.\nreturn unexpected output: '{output}'"
            )
            logger.error(self.log_prefix + message)
            raise exceptions.UnexpectedOutput(message)

    def execute_shell_command(
        self,  # NOSONAR
        command,
        timeout=0,
        wait_for_answer=True,
        omit_from_log=False,
        match=None,
        match_reg=None,
        command_echo=True,
        shows_output=False,
        endswith=("# ", "$ ", "> ", "#", ">"),
        _first_attempt=True,
        enter_key=True,
        reconnect=True,
        enter_char="\n",
        additional_cmd_failures=None,
        validate_output=True,
        **kwargs,
    ):  # NOSONAR
        """
        Execute a command via shell (router cli)
        :param shows_output: True - expecting command to return output, otherwise - will raise exceptions.UnexpectedOutput
        :param additional_cmd_failures: messages which indicate on error in output
        :param validate_output: if False, skip all output validations

        if doesn't have a prompt match - will raise exceptions.ExecutionTimeout
        :raises: ExecutionTimeout, SessionClosed
        """
        # save args and kwargs values for reconnect
        original_args = get_args_values(kwargs)

        if additional_cmd_failures is None:
            additional_cmd_failures = []
        else:
            additional_cmd_failures = return_as_list(additional_cmd_failures)

        timeout = timeout if timeout else self.command_timeout
        cmd = command if command_echo else ""
        if match_reg or match:
            # when match or match regex were provided, skipping the usual endswith prompt
            endswith = None
        if not match_reg:
            match = (
                rf".*{re.escape(match)}(.*)"
                if match
                else self.prompt.format(cmd=re.escape(cmd))
            )
        else:
            match = match_reg

        if reconnect and not self.is_connected():
            message = f"could not execute '{command}', session is not open. reconnecting and retrying execution"
            logger.debug(self.log_prefix + message)
            self.reconnect()

        if reconnect and self.shell is None:
            logger.debug(
                "Seems that channel was never initiated, opening the session first."
            )
            self.open_session()
            self._wait_for_prompt()

        channel = self.shell
        if not channel:
            raise exceptions.SessionClosed(
                f"Session is closed, channel was not instantiated"
            )
        channel.settimeout(timeout)
        channel.set_combine_stderr(True)
        output_lines = ""

        # Clear the buffer before executing any commands
        while channel.recv_ready():
            channel.recv(consts.MAX_BUFFER)
        if not omit_from_log:
            logger.debug(self.log_prefix + f"executing '{command}'")
        start_time = datetime.now()
        try:
            # execute the command
            channel.sendall(command + enter_char if enter_key else command)

            if not omit_from_log:
                logger.debug(
                    self.log_prefix + f"'{command}' execution is complete"
                )

            if wait_for_answer:
                time_start = monotonic()
                time_stop = time_start + timeout

                if match:
                    output_lines = self._read_until_match(
                        channel, time_stop, match=match, endswith=endswith
                    )
            else:
                message = f"executed: {command}. not pending for response."
                logger.debug(self.log_prefix + message)

        except TimeoutError as e:
            message = (
                f"Timeout reached - failed to execute command '{command}'"
            )
            logger.warning(self.log_prefix + message)
            raise exceptions.ExecutionTimeout(message, e)

        except OSError:
            logger.error(self.log_prefix + "SSH client exception occurs")
            if reconnect and _first_attempt and self.command_retry:
                logger.debug(
                    self.log_prefix + "session timed out, reconnecting."
                )
                self.reconnect()
                original_args["_first_attempt"] = (
                    False  # don't try to reconnect again on the second time
                )
                return self.execute_shell_command(**original_args)
            else:
                message = f"could not execute '{command}', session is not open"
                logger.error(self.log_prefix + message)
                raise exceptions.SessionClosed(message)

        if len(output_lines) and not omit_from_log:
            # logger.info(
            logger.debug(
                self.log_prefix + f"response to '{command}':\n{output_lines}"
            )

        if wait_for_answer:
            try:
                if match:
                    output_lines = self.output_validation(
                        output_lines,
                        command,
                        shows_output,
                        additional_cmd_failures,
                        validate_output,
                    )
            finally:
                if not omit_from_log:
                    # add log entry on how much time command was executed
                    time_diff = timedelta.total_seconds(
                        datetime.now() - start_time
                    )
                    logger.debug(
                        self.log_prefix
                        + f"command completed after {time_diff:.4f} seconds"
                    )
            return output_lines

    def _read_until_match(self, channel, time_stop, match="", endswith=None):
        output = ""
        last_output_len = len(output)
        # save the 'last_line' value in case 'endswith' is set, so that the buffer is read 1 more time before setting
        # the _match value. this is done to prevent chars in the middle of the output to be detected as and end.
        endswith_last_line = None
        while True:
            # True if data is buffered and ready to be read from this channel.
            # otherwise it means you may need to wait before more data arrives.
            while channel.recv_ready():
                # collect data from the ssh channel
                buffer = channel.recv(consts.MAX_BUFFER).decode(
                    "utf-8", "ignore"
                )  # 65936

                output += buffer

                if monotonic() > time_stop:
                    # Gets here if timeout has exceeded
                    break
            if last_output_len == len(output):
                # because of vt100 need to remove expected escape chars.
                # clean output from meta-characters that visualize output. (such as '\x1b[92m+]')
                output = self.strip_ansi_escape_codes(output)

                matches_list = match if isinstance(match, list) else [match]
                last_line = output.splitlines()
                for item in matches_list:
                    _match = None
                    if endswith and last_line:
                        if last_line[-1].endswith(endswith):
                            if last_line == endswith_last_line:
                                _match = re.match(item, output, re.DOTALL)
                            else:
                                endswith_last_line = last_line
                    else:
                        # On long output, matching could take a lot of time
                        _match = re.match(item, output, re.DOTALL)
                    if _match:
                        cmd_output = _match.group(1).rstrip()
                        return cmd_output

            # placed here to make sure that there is no more buffer to read, before trying to match the regex pattern.
            last_output_len = len(output)

            sleep(0.0025)
            if monotonic() > time_stop:
                message = f"command timeout exceeded and execution did not complete. Partial output:\n{output}"
                logger.error(self.log_prefix + message)
                raise exceptions.ExecutionTimeout(message, output)

    def send_char(
        self,
        char,
        multiple=None,
        match=None,
        command_echo=False,
        omit_from_log=True,
        shows_output=False,
        enter_key=False,
        exit_timeout_with_ctrl_c=False,
        **kwargs,
    ):
        """
        This is the final function to execute a char-key with 'execute_shell_command'
        """
        if multiple:
            char = char * int(multiple)

        char_in_hex = "".join(
            f"\\x{ord(c):02x}" for c in char
        )  # print in hex for debug
        logger.debug(self.log_prefix + f"Send chars '{char_in_hex}'..")
        return self.execute_shell_command(
            char,
            match=match,
            command_echo=command_echo,
            omit_from_log=omit_from_log,
            shows_output=shows_output,
            enter_key=enter_key,
            exit_timeout_with_ctrl_c=exit_timeout_with_ctrl_c,
            **kwargs,
        )

    def send_key(self, key, **kwargs):
        """
        Enter the requested key-sequence to the shell
        :type key: KeySequence
        """
        logger.debug(self.log_prefix + f"Pressing {key.name} key..")
        return self.send_char(key.value, **kwargs)

    def send_ctrl_c(self, **kwargs):
        return self.send_key(
            consts.KeySequence.CTRL_C, exit_timeout_with_ctrl_c=False, **kwargs
        )

    def send_ctrl_d(self, **kwargs):
        return self.send_key(consts.KeySequence.CTRL_D, **kwargs)

    def send_ctrl_z(self, **kwargs):
        return self.send_key(consts.KeySequence.CTRL_Z, **kwargs)

    def send_tab(self, omit_from_log=False, shows_output=True, **kwargs):
        return self.send_key(
            consts.KeySequence.TAB,
            omit_from_log=omit_from_log,
            shows_output=shows_output,
            **kwargs,
        )

    @staticmethod
    def strip_ansi_escape_codes(string_buffer):
        """
        Remove any ANSI (VT100) ESC codes from the output
        http://en.wikipedia.org/wiki/ANSI_escape_code
        """
        output = consts.ANSI_ESCAPE.sub("", string_buffer)
        output = consts.REMOVE_CHARS.sub("", output)

        return output

    def reconnect(self):
        # close session
        self.close()
        # reconnect
        self.connect_wait_for_prompt(self.prompt_retries)
