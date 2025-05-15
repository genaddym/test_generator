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

        # Find header line index and header columns
        header_line_index = None
        headers = []
        for i, line in enumerate(lines):
            if '|' in line and '-' not in line:
                header_line_index = i
                headers = [h.strip().lower().replace(' ', '_') for h in line.split('|')]
                break

        if header_line_index is None or not headers:
            return {'neighbors': []}

        # Data lines start after the separator line (which is after header line)
        # Find separator line index (line with only '-', '+', '|', and spaces)
        separator_line_index = None
        for i in range(header_line_index + 1, len(lines)):
            line = lines[i]
            if set(line.strip()) <= set('-+| '):
                separator_line_index = i
                break

        if separator_line_index is None:
            return {'neighbors': []}

        # Parse each data line after separator line until no more lines or empty lines
        for line in lines[separator_line_index + 1:]:
            if not line.strip():
                continue
            if '|' not in line:
                continue
            # Split line by '|' and strip each field
            fields = [field.strip() for field in line.split('|')]
            # Remove empty trailing fields caused by trailing '|'
            fields = [f for f in fields if f != '']

            # If number of fields less than headers, pad with empty strings
            if len(fields) < len(headers):
                fields += [''] * (len(headers) - len(fields))
            # If more fields than headers, truncate
            if len(fields) > len(headers):
                fields = fields[:len(headers)]

            # Map headers to fields
            neighbor = dict(zip(headers, fields))
            neighbors.append(neighbor)

        return {'neighbors': neighbors}