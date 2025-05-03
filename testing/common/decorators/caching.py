# pragma: exclude file
"""
Module providing caching functionality for function arguments.
This module allows storing and retrieving keyword arguments passed to functions,
which is useful for debugging, testing, and accessing previous function call parameters.
"""

import typing as t
import functools


class KwargsCache:
    """
    Cache for storing keyword arguments passed to functions.

    This class provides methods to store and retrieve keyword arguments
    from function calls, allowing access to parameters after the function
    has executed.
    """

    def __init__(self):
        self._kwargs_cache: t.Dict[str, t.Dict[str, t.Any]] = {}

    def get_cached_kwargs(self, cache_key: str):
        """
        Retrieve cached keyword arguments for a specific function.

        Args:
            cache_key: Identifier for the cached arguments

        Returns:
            Dictionary of keyword arguments that were passed to the function
        """
        return self._kwargs_cache[cache_key]

    @staticmethod
    def save_function_kwargs(cache_key: str):
        """
        Decorator that saves keyword arguments passed to a function.

        This decorator stores all keyword arguments in the instance's _kwargs_cache
        dictionary using the provided cache_key as the identifier.

        Args:
            cache_key: Identifier to use for storing the arguments

        Returns:
            Decorator function that wraps the target function
        """

        def deco(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                # Access to protected member is intentional here as this is part of the class's API
                # pylint: disable=protected-access
                self._kwargs_cache[cache_key] = kwargs
                return func(self, *args, **kwargs)

            return wrapper

        return deco
