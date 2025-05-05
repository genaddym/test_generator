from abc import ABC, abstractmethod

class DecipherBase(ABC):
    @abstractmethod
    def decipher(self, cli_output):
        pass

class ShowConfigProtocolsIsisInstanceInstanceIdAddressfamilyIpv6unicastTifastrerouteDecipher(DecipherBase):
    def decipher(self, cli_output):
        lines = cli_output.split('\r\n')
        result = {}
        for line in lines:
            if 'admin-state' in line:
                result['admin-state'] = line.split()[-1]
            elif 'protection-mode' in line:
                result['protection-mode'] = line.split()[-1]
        return result