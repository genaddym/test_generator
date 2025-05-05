from abc import ABC, abstractmethod

class DecipherBase(ABC):
    @abstractmethod
    def decipher(self, cli_output):
        pass

class ShowIsisInterfacesDecipher(DecipherBase):
    def decipher(self, cli_output):
        import re
        result = {}
        instance_id = None
        for line in cli_output.splitlines():
            if 'Instance' in line:
                instance_id = re.search(r'Instance (\d+):', line).group(1)
                result[instance_id] = []
            elif 'bundle-' in line:
                # Match interface name, state, type, and level using a more precise pattern
                match = re.match(r'\s*bundle-(\d+)\s+(\w+)\s+(\S+)\s+(\S+)', line)
                if match:
                    result[instance_id].append({
                        'Interface': f'bundle-{match.group(1)}',
                        'State': match.group(2),
                        'Type': match.group(3),
                        'Level': match.group(4)
                    })
        return result