# pragma: exclude file
"""
Module providing inspection-related decorators for function and method handling.
These decorators help with argument processing, signature inspection, and parameter validation.
"""

import inspect
import functools


def discard_unknown_args(func):
    """
    Decorator that filters out keyword arguments not defined in the function signature.

    This is useful when passing a dictionary of parameters to a function that only accepts
    a subset of those parameters, preventing TypeError for unexpected keyword arguments.

    Args:
        func: The function to decorate

    Returns:
        A wrapped function that only receives keyword arguments defined in its signature
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        signature = inspect.signature(func)
        allowed_parameters = list(signature.parameters)
        proper_kwargs = {
            k: v for k, v in kwargs.items() if k in allowed_parameters
        }
        return func(*args, **proper_kwargs)

    return wrapper
