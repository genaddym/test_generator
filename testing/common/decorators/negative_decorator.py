# pragma: exclude file
"""
Module providing a decorator for negative testing scenarios.
This decorator allows validation functions to be used for both positive and negative test cases,
checking if expected exceptions are raised under specific conditions.
"""

import collections
from functools import wraps

from orbital import common

logger = common.get_logger(__file__)


class NotRaisedException(Exception):
    """
    raises in case an expected exception wasn't raised during the validation process
    """


def negative(expected_exceptions=(Exception,)):
    """
    wrap validation in order to use same validation logic as negative test.
    negative validation check if an exception as raised, otherwise, NotRaisedException exception
    will raise. In addition, there is an option to look for specific exception message.

    after using the negative decorator, addition arguments should send to the function in order to
    invoke the negative behavior.

    the addition arguments are:
        negate_validation: specify if we expect for an exception from expected_exceptions
        matched_msg: if specified, checks if the exception message contain the text
        error_message: provides a custom failure message if the expected exception is not raised

    """
    KEY = "negate_validation"
    EXPECTED_MSG = "matched_msg"
    ERR_MSG = "error_message"

    # support single or multiple exceptions
    if isinstance(expected_exceptions, collections.abc.Iterable):
        expected_exceptions = tuple(expected_exceptions)
    elif expected_exceptions is not None:
        expected_exceptions = (expected_exceptions,)

    def negate_decorator(func):

        @wraps(func)
        def negate_function(*args, **kwargs):
            exceptions_names = ",".join(
                [exception.__name__ for exception in expected_exceptions]
            )
            default_err_msg = (
                f"Exception of types {exceptions_names} isn't raised during the function "
                f"'{func.__name__}' execution, although have expected."
            )

            # In case examining the content of the exception is not necessary,
            # an empty string will set
            matched_msg = kwargs.pop(EXPECTED_MSG, "")

            # default behavior of the validation is not to expect for failure
            negate_validation = bool(kwargs.pop(KEY, False))

            # which message sent in case of expected exception didn't raised
            err_msg = kwargs.pop(ERR_MSG, default_err_msg)

            if negate_validation:
                logger.info(
                    "The function '%s' was invoked with negate_validation attribute. "
                    "i.e. an exception should raise during the execution of this function..",
                    func.__name__,
                )
            try:
                result = func(*args, **kwargs)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                # Check if the caught exception is one of the expected types
                if not isinstance(e, expected_exceptions):
                    raise

                # check if an exception should raise
                if negate_validation:
                    # examining the content of the exception. i.e. if the content of exception is
                    # as expected
                    if matched_msg not in str(e):
                        raise NotRaisedException(
                            f"An exception type of '{e.__class__.__name__}' has raised but his "
                            f"content which is:'{str(e)}' don't contain in any way the expected"
                            f" content '{matched_msg}'"
                        ) from e
                    logger.info(
                        "An exception type of '%s' has raised as expected with message='%s'",
                        e.__class__.__name__,
                        str(e),
                    )
                # Throws forward the exception
                else:
                    raise

            # In case an exception didn't raise
            else:
                # check if failure was expected
                if negate_validation:
                    raise NotRaisedException(err_msg)
                return result

            return None  # Ensure consistent return statements

        return negate_function

    return negate_decorator
