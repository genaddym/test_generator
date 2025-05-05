from typing import Dict, Any


class DecipherBase:
    """
    Abstract base class for Decipher implementations.
    """
    def decipher(self, cli_output: str) -> Dict[str, Any]:
        raise NotImplementedError("Decipher method must be implemented by subclasses.")


class ShowConfigProtocolsIsisInstanceInstanceIdInterfaceInterfaceNameDecipher(DecipherBase):
    """
    Decipher class to parse 'show config protocols isis instance INSTANCE_ID interface INTERFACE_NAME' CLI output.
    Extracts fast-reroute configuration per address family for the specified interface.
    """

    def decipher(self, cli_output: str) -> Dict[str, Any]:
        """
        Parses the CLI output and returns a dictionary representing the fast-reroute configuration
        for each address family under the specified interface.

        Args:
            cli_output (str): Raw CLI output string.

        Returns:
            Dict[str, Any]: Parsed fast-reroute configuration keyed by address family.
        """
        result = {}
        lines = cli_output.splitlines()
        current_af = None
        in_interface = False
        in_address_family = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("interface "):
                in_interface = True
                in_address_family = False
                current_af = None
            elif in_interface and stripped.startswith("address-family "):
                # Extract address family name
                parts = stripped.split()
                if len(parts) >= 2:
                    current_af = parts[1]
                    in_address_family = True
                    if current_af not in result:
                        result[current_af] = {}
            elif in_address_family:
                if stripped.startswith("fast-reroute backup-candidate"):
                    # Extract enabled/disabled status
                    parts = stripped.split()
                    if len(parts) >= 3:
                        status = parts[-1]
                        result[current_af]["fast-reroute backup-candidate"] = status == "enabled"
                elif stripped.startswith("metric level"):
                    # Extract metric level and value
                    parts = stripped.split()
                    # Expected format: metric level level-2 2000
                    if len(parts) == 4:
                        level_key = parts[2]
                        try:
                            metric_value = int(parts[3])
                        except ValueError:
                            metric_value = None
                        if "metric level" not in result[current_af]:
                            result[current_af]["metric level"] = {}
                        result[current_af]["metric level"][level_key] = metric_value
                elif stripped == "!":
                    # End of address-family block
                    in_address_family = False
                    current_af = None
            elif stripped == "!":
                # End of interface block
                in_interface = False
                in_address_family = False
                current_af = None

        return result