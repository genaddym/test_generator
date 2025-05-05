class DecipherBase:
    """
    Abstract base class for Decipher implementations.
    """
    def decipher(self, cli_output: str):
        raise NotImplementedError("Subclasses must implement this method")

class ShowConfigProtocolsIsisDecipher(DecipherBase):
    """
    Decipher class to parse 'show config protocols isis' CLI output
    and extract the ISIS Instance ID.
    """

    def decipher(self, cli_output: str):
        """
        Parse the CLI output and return the ISIS Instance ID as an integer.

        Args:
            cli_output (str): Raw CLI output string.

        Returns:
            int: ISIS Instance ID if found, else None.
        """
        lines = cli_output.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("instance "):
                parts = line.split()
                if len(parts) == 2 and parts[0] == "instance":
                    try:
                        return int(parts[1])
                    except ValueError:
                        return None
        return None