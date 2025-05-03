# pragma: exclude file
"""
Module providing validation utilities for data type checking and conversion.
This module contains functions for validating and converting data types,
handling collections, and ensuring proper data formats.
"""


def return_as_list(obj, convert_none_to_empty_list=False):
    """
    in case obj is not a list or a tuple, create a list, append obj to the list and return it.
    :param obj: the object we expect to be a list
    :param convert_none_to_empty_list: A flag which indicates
     to return an empty list in case of None value
    :return: list
    """
    if obj is None and convert_none_to_empty_list:
        return []
    if not isinstance(obj, (list, tuple, set)) or isnamedtupleinstance(obj):
        return [obj]
    return obj


def isnamedtupleinstance(x):
    """
    check if an object is an instance of a namedtuple?
    :return: bool
    """
    t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple:
        return False
    f = getattr(t, "_fields", None)
    if not isinstance(f, tuple):
        return False
    return all(isinstance(n, str) for n in f)
