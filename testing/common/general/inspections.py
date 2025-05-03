# pragma: exclude file
"""
Module providing inspection utilities for examining Python objects.
This module contains functions for inspecting function signatures, parameters,
and other object attributes to support dynamic behavior and introspection.
"""

import inspect


def get_default_args(func):
    """
    Get the default arguments of a function.
    :param func: function to inspect
    :return: a dict of all default args in a function
    """
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def get_args_values(kwargs=None):
    """
    :param kwargs: add kwargs to arguments, optional
    :return: dict of {arg: value}. can be used as 'func(**return_value)'
    """
    frame = inspect.stack()[1].frame  # retrieve called function from stack
    _args, _, _, values = inspect.getargvalues(frame)
    args = {key: value for key, value in values.items() if key in _args}
    if kwargs:
        args.update(kwargs)
    args.pop("self", None)
    return args
