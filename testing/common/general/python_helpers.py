# pragma: exclude file
"""
Module providing general Python helper functions and utilities.
This module contains various utility functions for attribute access, dictionary manipulation,
singleton pattern implementation, and list operations.
"""

import threading
import collections
from copy import deepcopy


def getattr_deep(obj, names, *default):
    """
    get attribute for multiple hierarchies in an object.
    :param obj: Object to get attributes from
    :type obj: Object
    :param names: a list of attribute names to search in obj, such as ['company', 'worker', 'job']
    :type names: list of str or str
    :param default: optional default value to return if attribute not found
    :type default: Object
    :return: found attribute or default value
    :raises: AttributeError if attr not found and no default value provided
    """
    if len(default) > 1:
        raise TypeError("only a single default value is allowed")
    if isinstance(names, str):
        names = [names]
    _attr = obj
    for name in names:
        try:
            _attr = getattr(_attr, name)
        except AttributeError:
            if default:
                return default[0]
            raise
    return _attr


def trim_dict(dict_to_trim, dict_to_remove):
    """
    remove a dict from another dict
    :param dict_to_trim: dict to remove items from
    :param dict_to_remove: dict of items to remove
    :return:
    """
    return {k: v for k, v in dict_to_trim.items() if k not in dict_to_remove}


class Singleton(type):
    """
    Metaclass for implementing the Singleton pattern.

    This metaclass ensures that only one instance of a class is created.
    All subsequent instantiations return the same instance.
    """

    _instances = {}

    def __init__(cls, *args, **kwargs):
        cls._lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def merge(original_dict, update_dict):
    """
    Return a new dictionary by merging two dictionaries recursively.
    update_dict will be merged to original_dict
    """
    result = deepcopy(original_dict)

    for key, value in update_dict.items():
        if isinstance(value, collections.abc.Mapping):
            result[key] = merge(result.get(key, {}), value)
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                try:
                    result.setdefault(key, [])[i].update(item)
                    result[key][i].update(item)
                except (IndexError, KeyError, AttributeError):
                    result[key].append(
                        item
                    )  # in case item only exists in update_dict, create a new list
        else:
            result[key] = deepcopy(update_dict[key])

    return result


def flat_list(lst):
    """
    Convert a nested list into flat list
    -> For example:
        [item1, item2, [item3, item4, [item5]], [item6], [], [[]], [[item7]]]
    -> will be converted to:
        [item1, item2, item3, item4, item5, item6, item7]
    :type lst: list
    :return: the converted list
    """
    if not any(isinstance(item, list) for item in lst):
        return lst
    flat_lst = []

    for item in lst:
        if isinstance(item, list):
            flat_lst.extend(flat_list(item))
        else:
            flat_lst.append(item)

    return flat_lst
