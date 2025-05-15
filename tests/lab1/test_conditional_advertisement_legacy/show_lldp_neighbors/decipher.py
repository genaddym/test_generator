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
        lines = cli_response.strip().split('\n')
        headers = []
        for line in lines:
            if '|' in line and '-' not in line:
                headers = [header.strip().lower().replace(' ', '_') for header in line.split('|')]
                break

        data_start = False
        for line in lines:
            if '-' in line and '+' in line:
                data_start = True
                continue
            if data_start and '|' in line:
                values = [value.strip() for value in line.split('|')]
                if len(values) == len(headers):
                    neighbor = dict(zip(headers, values))
                    neighbors.append(neighbor)

        return {'neighbors': neighbors}