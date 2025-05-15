from tests.base.decipher import Decipher
import re

class ShowConfigInterfacesInterfaceNameDecipher(Decipher):
    """
    Parser for "show config interfaces INTERFACE_NAME" command
    """

    @staticmethod
    def decipher(cli_response: str):
        """
        Parses the CLI response to extract the bundle_id value.

        Args:
            cli_response (str): Raw CLI output string.

        Returns:
            dict: Parsed data with bundle_id key.
        """
        bundle_id = None
        match = re.search(r'^\s*bundle-id\s+(\d+)', cli_response, re.MULTILINE)
        if match:
            bundle_id = int(match.group(1))
        return {"bundle_id": bundle_id}