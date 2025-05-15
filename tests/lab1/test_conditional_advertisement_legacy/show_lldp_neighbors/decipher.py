from tests.base.decipher import Decipher
from typing import List, Dict


class ShowLldpNeighborsDecipher(Decipher):
    """
    Parser for "show lldp neighbors" command
    """

    @staticmethod
    def decipher(cli_response: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse the 'show lldp neighbors' CLI output into structured JSON.

        Args:
            cli_response (str): Raw CLI output string.

        Returns:
            dict: Parsed output with key 'neighbors' containing list of neighbor dicts.
        """
        neighbors = []
        lines = [line.rstrip() for line in cli_response.strip().splitlines() if line.strip()]
        # Find the separator line index (line with dashes and pluses)
        separator_index = None
        for idx, line in enumerate(lines):
            if set(line.strip()) <= set("-+"):
                separator_index = idx
                break
        if separator_index is None or separator_index == 0:
            return {"neighbors": neighbors}

        # Header line is the line before separator
        header_line = lines[separator_index - 1]
        # Split header by '|' and normalize keys
        headers = [h.strip().lower().replace(" ", "_") for h in header_line.split("|")]
        # Data lines start after separator line
        data_lines = lines[separator_index + 1 :]

        for line in data_lines:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            # Remove empty trailing parts caused by trailing '|'
            if parts and parts[-1] == "":
                parts = parts[:-1]
            if len(parts) != len(headers):
                continue
            neighbor = dict(zip(headers, parts))
            neighbors.append(neighbor)

        return {"neighbors": neighbors}