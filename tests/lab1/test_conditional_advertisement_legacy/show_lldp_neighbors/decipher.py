from tests.base.decipher import Decipher

class ShowLldpNeighborsDecipher(Decipher):
    """
    Parser for "show lldp neighbors" command
    """

    @staticmethod
    def decipher(cli_response: str):
        """
        Decipher the CLI output of 'show lldp neighbors' command into a JSON dict.
        """
        result = {}
        neighbors = []

        lines = cli_response.strip().splitlines()
        separator_index = None
        for i, line in enumerate(lines):
            if set(line.strip()) <= set("-+|"):
                separator_index = i
                break

        if separator_index is None:
            result["lldp_neighbors"] = neighbors
            return result

        data_lines = lines[separator_index + 1:]

        for line in data_lines:
            if not line.strip() or set(line.strip()) <= set("-+|"):
                continue
            parts = [part.strip() for part in line.split('|')]
            if len(parts) < 4:
                continue
            interface, neighbor_system_name, neighbor_interface, neighbor_ttl = parts[:4]

            neighbor_entry = {
                "interface": interface,
                "neighbor_system_name": neighbor_system_name,
                "neighbor_interface": neighbor_interface,
                "neighbor_ttl": neighbor_ttl
            }
            neighbors.append(neighbor_entry)

        result["lldp_neighbors"] = neighbors
        return result