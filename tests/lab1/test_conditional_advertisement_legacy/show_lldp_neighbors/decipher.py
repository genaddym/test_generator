from tests.base.decipher import Decipher

class ShowLldpNeighborsDecipher(Decipher):
    """
    Parser for the 'show lldp neighbors' CLI command.
    """

    @staticmethod
    def decipher(cli_response: str):
        """
        Parse the 'show lldp neighbors' CLI output into structured JSON.

        Args:
            cli_response (str): Raw CLI output string.

        Returns:
            dict: Parsed output with key 'neighbors' containing list of neighbor dicts.
        """
        neighbors = []
        lines = cli_response.strip().splitlines()
        headers = []
        # Find header line (contains '|') and not separator line
        for line in lines:
            if '|' in line and '-' not in line:
                headers = [h.strip().lower().replace(' ', '_') for h in line.split('|')]
                break

        # Find index of separator line (with '-' and '+')
        separator_index = None
        for i, line in enumerate(lines):
            if set(line.strip()) <= set('-+| '):
                separator_index = i
                break

        if not headers or separator_index is None:
            return {'neighbors': []}

        # Parse data lines after separator line
        for line in lines[separator_index + 1:]:
            if '|' not in line:
                continue
            values = [v.strip() for v in line.split('|')]
            # Remove empty strings from split if any trailing '|'
            values = [v for v in values if v != '']
            if len(values) != len(headers):
                # Sometimes trailing empty columns cause mismatch, skip line
                continue
            neighbor = dict(zip(headers, values))
            neighbors.append(neighbor)

        return {'neighbors': neighbors}