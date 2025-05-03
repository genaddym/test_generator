"""
Device utilities for testing.
"""


def validate_device_name(device_name: str | None):
    """
    Checks whether the device name is None or not.
    Raises ValueError if the device name is None.
    """
    if device_name is None:
        raise ValueError("Device name cannot be None")


def remove_domain_name(device_name: str) -> str:
    """
    Remove the domain name <.comcast.net> from the device name.
    """
    validate_device_name(device_name)
    return device_name.removesuffix(".comcast.net")


def get_site_name(device_name: str) -> str:
    """
    Get the site name from the device name.
    The site name is the part of the device name after the first dot.

    Example:
        device_name = "device.site10.cran1"
        site_name = get_site_name(device_name)
        print(site_name)  # Output: "site10.cran1"
    """
    validate_device_name(device_name)
    device_name = remove_domain_name(device_name)
    if "." not in device_name:
        return ""
    return device_name.split(".", maxsplit=1)[-1]


def get_device_name(device_name: str) -> str:
    """
    Get the device name from the device name.
    The device name is the part of the device name before the first dot.

    Example:
        device_name = "device.site10.cran1"
        site_name = get_device_name(device_name)
        print(site_name)  # Output: "device"
    """
    validate_device_name(device_name)
    return device_name.split(".", maxsplit=1)[0]


def compare_device_names(device_name1: str, device_name2: str) -> bool:
    """
    Compare two device names
    Each device name is tokenized by the dot (.) separator.
    The comparison is done token by token.
    The comparison is case insensitive.

    Example:
        device_name1 = "device.site10.cran1"
        device_name2 = "DEVICE.SITE10.Cran1.comcast.net"
        result = compare_device_names(device_name1, device_name2)
        print(result)  # Output: True

        device_name1 = "device.site10.cran1"
        device_name2 = "device.site10.cran2.comcast.net"
        result = compare_device_names(device_name1, device_name2)
        print(result)  # Output: False
    """

    def tokenize(device_name: str) -> list[str]:
        """
        Tokenize the device name into a list of tokens.
        The tokens are separated by dots.
        """
        return device_name.split(".")

    validate_device_name(device_name1)
    validate_device_name(device_name2)
    device1_tokens = tokenize(device_name1.lower())
    device2_tokens = tokenize(device_name2.lower())

    for token1, token2 in zip(device1_tokens, device2_tokens):
        if token1 != token2:
            return False
    if bool(device1_tokens) != bool(device2_tokens):
        return False
    return True
