# pragma: exclude file
"""
Module defining constants used by decorators in the Orbital testing framework.
These constants control timing, retry behavior, and timeout settings for various operations.
"""

SECONDS_BETWEEN_COMMANDS = 1  # time to wait between each wait() iteration

EXTRA_TIMEOUT_SECONDS = 120  # wait for process to finish naturally

# default parameters in retry function
SECONDS_DELAY_BETWEEN_ATTEMPTS = 1
MAX_SECONDS_DELAY_IN_RETRY = 60
DEFAULT_TRIES_NUM = 5
MULTIPLIER_DELAY_IN_RETRY = 1
