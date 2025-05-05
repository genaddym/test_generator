from abc import ABC, abstractmethod
import re

class Decipher(ABC):
    """
    Abstract base class for Decipher implementations.
    """

    @abstractmethod
    def decipher(self, cli_output: str) -> dict:
        pass

class ShowIsisInstanceInstanceIdDecipher(Decipher):
    """
    Decipher class to parse 'show isis instance INSTANCE_ID' CLI output,
    extracting the TI-LFA operational status per address family.
    """

    def decipher(self, cli_output: str) -> dict:
        """
        Parse the TI-LFA section from the CLI output and return a dictionary
        representing the TI-LFA operational status per address family.

        Args:
            cli_output (str): Raw CLI output string.

        Returns:
            dict: Parsed TI-LFA status with keys 'IPv4' and 'IPv6' and their details.
        """
        ti_lfa_dict = {}
        # Extract the TI-LFA section
        ti_lfa_match = re.search(r"TI-LFA:\r?\n((?:\s+.+\r?\n?)+)", cli_output)
        if not ti_lfa_match:
            return ti_lfa_dict

        ti_lfa_section = ti_lfa_match.group(1)
        # Each line in TI-LFA section
        for line in ti_lfa_section.splitlines():
            line = line.strip()
            # Match lines like: IPv4                : disabled
            m = re.match(r"(\S+)\s*:\s*(.+)", line)
            if m:
                af = m.group(1)
                status = m.group(2)
                # For IPv4 and IPv6, parse status and additional info if present
                if af in ("IPv4", "IPv6"):
                    # Status may have commas and additional info
                    parts = [p.strip() for p in status.split(",")]
                    # First part is main status
                    main_status = parts[0]
                    details = {}
                    # Parse additional flags and key-value pairs
                    for part in parts[1:]:
                        # key-value pairs separated by space or dash
                        if "maximum-labels" in part:
                            # e.g. maximum-labels 3
                            kv_match = re.search(r"maximum-labels\s+(\d+)", part)
                            if kv_match:
                                details["maximum-labels"] = int(kv_match.group(1))
                        elif "link-protection" in part:
                            details["link-protection"] = True
                        else:
                            # other flags
                            details[part] = True
                    ti_lfa_dict[af] = {"status": main_status}
                    ti_lfa_dict[af].update(details)
        return ti_lfa_dict