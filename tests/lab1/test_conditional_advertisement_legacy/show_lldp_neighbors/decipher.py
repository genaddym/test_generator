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
        lines = cli_response.strip().splitlines()
        # Find the line index where header separator is (line with dashes and pluses)
        separator_index = None
        for idx, line in enumerate(lines):
            if set(line.strip()) <= set("-+| "):
                separator_index = idx
                break
        if separator_index is None:
            return {"neighbors": neighbors}

        # Header line is one line above separator
        header_line = lines[separator_index - 1]
        # Determine column positions by splitting header line by '|'
        headers = [h.strip().lower().replace(" ", "_") for h in header_line.split("|")]
        # Expected headers: interface, neighbor_system_name, neighbor_interface, neighbor_ttl

        # Data lines start after separator line
        data_lines = lines[separator_index + 1:]

        for line in data_lines:
            if not line.strip():
                continue
            # Split line by '|'
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            # Map parts to headers
            neighbor = {}
            for i, key in enumerate(headers):
                if i < len(parts):
                    neighbor[key] = parts[i]
                else:
                    neighbor[key] = ""
            neighbors.append(neighbor)

        return {"neighbors": neighbors}