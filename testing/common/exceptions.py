# pragma: exclude file
"""
Module defining exception classes for the Orbital testing framework.
This module provides a hierarchy of exceptions for handling various error conditions
during testing, SSH connections, command execution, and topology operations.
"""

from paramiko import SSHException as se


class UnknownCliException(Exception):
    """
    Exception raised when an unknown CLI error occurs.
    This is a general exception for CLI-related errors that don't fit other categories.
    """


class CommitFailedException(Exception):
    """
    Exception raised when a configuration commit operation fails.
    This typically occurs when a device rejects configuration changes during the commit phase.
    """


class OrbitalTemplateException(Exception):
    """
    Exception raised when there's an error with Orbital templates.
    This can occur during template rendering, validation, or application.
    """


class TopologyException(Exception):
    """
    Exception raised when there's an error with the network topology.
    This can occur during topology discovery, validation, or manipulation.
    """


FileExceptions = (FileNotFoundError, PermissionError, OSError)

# - SSHException
# |
# |-- CommandFailed
#    |-- ExecutionTimeout
#    |-- ExecutionFailed
#    |-- UnexpectedOutput
# |-- ConnectionFail
#    |-- BadCredentials
#    |-- PromptException
# |-- SessionClosed
# - SCPException


class MainException(AssertionError):
    """
    Base exception class for all main Orbital testing exceptions.
    Inherits from AssertionError to provide compatibility with assertion-based testing.
    """


class SigKillTimeout(TimeoutError):
    """
    Thrown when 'wait' decorator is killing a process with SIGKILL.
    This exception indicates that a process had to be forcibly terminated.
    """

    def __init__(
        self, value="Timed Out"
    ):  # init required by the parent 'wait'
        self.value = value

    def __str__(self):
        return repr(self.value)


class RetryException(MainException):
    """
    Exception raised when a retry operation fails.
    This is typically used in retry loops to indicate that all retry attempts have failed.
    """


class SSHException(MainException, se):
    """
    Base exception for all SSH-related errors.
    Inherits from both MainException and paramiko's SSHException.
    """


class CommandFailed(SSHException):
    """
    Exception raised when a command execution fails.
    This is a base class for more specific command execution failures.
    """


class ExecutionTimeout(CommandFailed):
    """
    Exception raised when a command execution times out.
    This occurs when a command takes longer than the specified timeout period.
    """

    def __init__(self, msg, output=None):
        self.message = msg
        self.output = output


class ExecutionFailed(CommandFailed):
    """
    Exception raised when a command execution fails with an error.
    This typically occurs when a command returns a non-zero exit code.
    """


class UnexpectedOutput(CommandFailed):
    """
    Exception raised when a command produces unexpected output.
    This occurs when the output doesn't match expected patterns or formats.
    """


class ConnectionFail(SSHException):
    """
    Exception raised when an SSH connection cannot be established.
    This is a base class for more specific connection failures.
    """


class BadCredentials(ConnectionFail):
    """
    Exception raised when authentication fails due to invalid credentials.
    This typically occurs with incorrect usernames or passwords.
    """


class PromptException(ConnectionFail):
    """
    Exception raised for prompt failures, such as endless 'CLI LOADING'.
    This occurs when the expected command prompt is not received or recognized.
    """


class SessionClosed(SSHException):
    """
    Exception raised when an operation is attempted on a closed SSH session.
    This occurs when trying to use a session that has been terminated.
    """


class OperationNotSupported(Exception):
    """
    Exception raised when an operation is not supported by the current implementation.
    This is used to indicate that a feature or function is not available.
    """
