# pragma: exclude file
"""
Common regular expressions used across the project
"""

# Network related patterns
IPV4_PATTERN = (
    r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
)
