from abc import ABC, abstractmethod

class DecipherBase(ABC):
    @abstractmethod
    def decipher(self, cli_output):
        pass

class ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv4unicastTifastrerouteDecipher(DecipherBase):
    def decipher(self, cli_output):
        lines = cli_output.splitlines()
        result = {}
        for line in lines:
            if "admin-state" in line:
                result['admin_state'] = line.split()[-1]
            elif "protection-mode" in line:
                result['protection_mode'] = line.split()[-1]
        return result