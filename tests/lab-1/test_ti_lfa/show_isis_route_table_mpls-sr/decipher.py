import re
from typing import Dict, Any, List
from decipher_base import Decipher

class ShowIsisRouteTableMplssrDecipher(Decipher):
    """
    Decipher class for 'show isis route table mpls-sr' command output.
    Parses the segment-routing MPLS table per ISIS instance and address family.
    """

    def decipher(self, raw_output: str) -> Dict[str, Any]:
        """
        Parses the raw CLI output and returns structured data as a dictionary.

        Returns a dict with keys as instance IDs, each containing 'ipv4' and 'ipv6' keys
        with lists of route entries.
        """
        result: Dict[str, Any] = {}
        lines = raw_output.splitlines()

        instance_re = re.compile(r"^\s*Instance\s+(\d+)")
        af_re = re.compile(r"^\s*(ipv4|ipv6) segment-routing mpls table:")
        level_re = re.compile(r"^\s*Level\s*-\s*(\d+)")
        header_re = re.compile(r"^\s*Destination\s+Prefix\s+algorithm\s+cost\s+tag\s+priority\s+nh-address\s+interface\s+interface-weight\s+egress-label\s+Nexthop-srgb-base")
        # The header line may be missing or have variable columns, so we parse entries flexibly.

        current_instance = None
        current_af = None
        current_level = None
        entries: List[Dict[str, Any]] = []

        # Helper function to parse a route entry block (one or more lines)
        def parse_route_block(block_lines: List[str]) -> List[Dict[str, Any]]:
            parsed_entries = []
            # The first line contains destination, prefix, algorithm, cost, tag, priority, nh-address, interface, interface-weight, egress-label, Nexthop-srgb-base
            # Subsequent lines may contain additional next hops with partial info.
            # We'll parse by columns based on fixed widths or by splitting and filling missing fields.

            # We will parse each line by splitting on whitespace but keep in mind nh-address may contain spaces (e.g. with (lp))
            # Strategy: Use regex to capture fields carefully.

            # Regex pattern for a full route line:
            # Destination (optional), Prefix (optional), algorithm, cost, tag, priority, nh-address (may contain spaces and parentheses),
            # interface, interface-weight, egress-label, Nexthop-srgb-base
            # Because many fields can be missing, we parse line by line and fill missing fields from previous line.

            # We'll parse the first line fully, then subsequent lines only have partial fields.

            last_entry = None
            for idx, line in enumerate(block_lines):
                # Clean line
                line = line.rstrip()
                if not line.strip():
                    continue
                # Split line by whitespace but keep nh-address with parentheses as one field
                # We'll try to parse by columns using regex groups

                # Pattern explanation:
                # Optional Destination: non-space string at start
                # Optional Prefix: non-space string
                # Algorithm: non-space string
                # Cost: number
                # Tag: non-space string
                # Priority: non-space string
                # NH-address: can be IP with optional (lp), so match until next known field (interface)
                # Interface: non-space string
                # Interface-weight: non-space string
                # Egress-label: non-space string or N/A
                # Nexthop-srgb-base: non-space string or empty

                # Because fields can be missing, we parse by position and fallback to previous values.

                # We'll split line into tokens, but nh-address may have spaces due to (lp) etc.
                tokens = line.split()
                # Heuristic: if first token is a number or IP, it's destination or prefix
                # We'll try to parse first line fully, subsequent lines partially.

                if idx == 0:
                    # First line: try to parse all fields
                    # We expect at least 7 tokens before nh-address: Destination, Prefix, algorithm, cost, tag, priority
                    # But sometimes Destination or Prefix missing, so we check tokens count

                    # We'll try to find algorithm token by looking for known algorithms or numeric cost

                    # Find algorithm index (first token that is not a number and not IP)
                    # But algorithm can be 'spf' or '128' (seen in example), so treat algorithm as token after prefix/destination

                    # We'll try to parse as:
                    # Destination (optional), Prefix (optional), algorithm, cost, tag, priority, nh-address, interface, interface-weight, egress-label, Nexthop-srgb-base

                    # Because Destination and Prefix can be missing, we try to detect algorithm token by known values or position

                    # We'll try to parse from right to left for known fields: interface, interface-weight, egress-label, Nexthop-srgb-base

                    # From right:
                    # last token: Nexthop-srgb-base (optional)
                    # before last: egress-label (optional)
                    # before that: interface-weight
                    # before that: interface
                    # before that: nh-address (may be multiple tokens)
                    # before that: priority
                    # before that: tag
                    # before that: cost
                    # before that: algorithm
                    # before that: prefix
                    # before that: destination

                    # We'll parse from right to left:

                    nexthop_srgb_base = None
                    egress_label = None
                    interface_weight = None
                    interface = None
                    nh_address = None
                    priority = None
                    tag = None
                    cost = None
                    algorithm = None
                    prefix = None
                    destination = None

                    # Start from right
                    # We expect at least 6 tokens at right side: priority, nh-address, interface, interface-weight, egress-label, nexthop-srgb-base
                    # But nh-address can be multiple tokens

                    # We'll parse last tokens for nexthop_srgb_base and egress_label if they look numeric or N/A

                    # We'll try to parse last tokens as:
                    # If last token is numeric or 0, it's nexthop_srgb_base
                    # Before that egress_label (can be N/A or number)
                    # Before that interface_weight (can be N/A or number)
                    # Before that interface (string)
                    # Before that nh-address (can be multiple tokens)
                    # Before that priority, tag, cost, algorithm, prefix, destination

                    # We'll parse from right:

                    # Initialize index from right
                    idx_right = len(tokens) - 1

                    # nexthop_srgb_base
                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right] == '0'):
                        nexthop_srgb_base = tokens[idx_right]
                        idx_right -= 1
                    else:
                        nexthop_srgb_base = None

                    # egress_label
                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right].upper() == 'N/A'):
                        egress_label = tokens[idx_right]
                        idx_right -= 1
                    else:
                        egress_label = None

                    # interface_weight
                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right].upper() == 'N/A'):
                        interface_weight = tokens[idx_right]
                        idx_right -= 1
                    else:
                        interface_weight = None

                    # interface
                    if idx_right >= 0:
                        interface = tokens[idx_right]
                        idx_right -= 1
                    else:
                        interface = None

                    # Now nh-address: from start of nh-address to idx_right
                    # nh-address may contain spaces and parentheses, so we collect tokens from idx_right down to priority token

                    # priority token is before tag, cost, algorithm, prefix, destination

                    # We expect priority, tag, cost, algorithm to be 4 tokens before nh-address

                    # So priority index is idx_right

                    # We'll parse priority, tag, cost, algorithm from tokens at idx_right, idx_right-1, idx_right-2, idx_right-3

                    if idx_right - 3 >= 0:
                        priority = tokens[idx_right]
                        tag = tokens[idx_right - 1]
                        cost = tokens[idx_right - 2]
                        algorithm = tokens[idx_right - 3]
                        idx_right -= 4
                    else:
                        priority = None
                        tag = None
                        cost = None
                        algorithm = None

                    # Now prefix and destination are tokens from start to idx_right

                    if idx_right >= 1:
                        destination = tokens[0]
                        prefix = tokens[1]
                    elif idx_right == 0:
                        destination = tokens[0]
                        prefix = None
                    else:
                        destination = None
                        prefix = None

                    # nh-address tokens are tokens from idx_right+1 to interface token index -1

                    # We have interface at idx_right+1 (already taken), so nh-address tokens are tokens from idx_right+1 to interface token index -1

                    # But we already assigned interface at idx_right+1, so nh-address tokens are tokens from idx_right+1+1 to interface token index -1? This is ambiguous.

                    # Because of complexity, we reconstruct nh-address from tokens between priority and interface

                    # We'll reconstruct nh-address as tokens from idx_right+4 to interface token index -1

                    # But we have no exact indexes, so we reconstruct nh-address as tokens between algorithm and interface

                    # We'll reconstruct nh-address as tokens from index 4 to index of interface -1

                    # Let's find interface index

                    try:
                        interface_index = tokens.index(interface)
                    except ValueError:
                        interface_index = len(tokens) - 4  # fallback

                    nh_address_tokens = tokens[4:interface_index]
                    nh_address = " ".join(nh_address_tokens) if nh_address_tokens else None

                    entry = {
                        "destination": destination,
                        "prefix": prefix,
                        "algorithm": algorithm,
                        "cost": int(cost) if cost and cost.isdigit() else None,
                        "tag": tag,
                        "priority": priority,
                        "nh_address": nh_address,
                        "interface": interface,
                        "interface_weight": int(interface_weight) if interface_weight and interface_weight.isdigit() else None,
                        "egress_label": egress_label,
                        "nexthop_srgb_base": int(nexthop_srgb_base) if nexthop_srgb_base and nexthop_srgb_base.isdigit() else None,
                    }
                    parsed_entries.append(entry)
                    last_entry = entry
                else:
                    # Subsequent lines: partial entries, usually next hops
                    # They usually start with spaces and then cost, tag, priority, nh-address, interface, interface-weight, egress-label, nexthop_srgb_base
                    # Destination, prefix, algorithm missing

                    # We'll parse from right as before

                    tokens = line.strip().split()
                    idx_right = len(tokens) - 1

                    nexthop_srgb_base = None
                    egress_label = None
                    interface_weight = None
                    interface = None
                    nh_address = None
                    priority = None
                    tag = None
                    cost = None

                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right] == '0'):
                        nexthop_srgb_base = tokens[idx_right]
                        idx_right -= 1
                    else:
                        nexthop_srgb_base = None

                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right].upper() == 'N/A'):
                        egress_label = tokens[idx_right]
                        idx_right -= 1
                    else:
                        egress_label = None

                    if idx_right >= 0 and (tokens[idx_right].isdigit() or tokens[idx_right].upper() == 'N/A'):
                        interface_weight = tokens[idx_right]
                        idx_right -= 1
                    else:
                        interface_weight = None

                    if idx_right >= 0:
                        interface = tokens[idx_right]
                        idx_right -= 1
                    else:
                        interface = None

                    # Now priority, tag, cost, nh-address remain

                    if idx_right - 2 >= 0:
                        priority = tokens[idx_right]
                        tag = tokens[idx_right - 1]
                        cost = tokens[idx_right - 2]
                        idx_right -= 3
                    else:
                        priority = None
                        tag = None
                        cost = None

                    # nh-address is tokens from start to idx_right

                    nh_address_tokens = tokens[:idx_right + 1] if idx_right >= 0 else []
                    nh_address = " ".join(nh_address_tokens) if nh_address_tokens else None

                    # Build entry by copying destination, prefix, algorithm from last_entry

                    if last_entry:
                        entry = {
                            "destination": last_entry.get("destination"),
                            "prefix": last_entry.get("prefix"),
                            "algorithm": last_entry.get("algorithm"),
                            "cost": int(cost) if cost and cost.isdigit() else None,
                            "tag": tag,
                            "priority": priority,
                            "nh_address": nh_address,
                            "interface": interface,
                            "interface_weight": int(interface_weight) if interface_weight and interface_weight.isdigit() else None,
                            "egress_label": egress_label,
                            "nexthop_srgb_base": int(nexthop_srgb_base) if nexthop_srgb_base and nexthop_srgb_base.isdigit() else None,
                        }
                        parsed_entries.append(entry)
                        last_entry = entry
            return parsed_entries

        # Main parsing loop
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            m_instance = instance_re.match(line)
            if m_instance:
                current_instance = m_instance.group(1)
                if current_instance not in result:
                    result[current_instance] = {"ipv4": [], "ipv6": []}
                current_af = None
                current_level = None
                i += 1
                continue

            m_af = af_re.match(line)
            if m_af:
                current_af = m_af.group(1)
                current_level = None
                i += 1
                continue

            m_level = level_re.match(line)
            if m_level:
                current_level = m_level.group(1)
                i += 1
                continue

            # Skip legend and header lines
            if line.startswith("Legend:") or line.startswith("Destination") or line.startswith("Level") or line.startswith("Instance") or line.startswith("ipv4") or line.startswith("ipv6"):
                i += 1
                continue

            # Parse route entries
            # Route entries start with a line that may start with a number (destination) or spaces (next hop)

            # Collect block lines for one route entry (including next hops)
            if current_instance and current_af:
                block_lines = []
                # First line of block
                block_lines.append(lines[i])
                i += 1
                # Collect subsequent lines that start with spaces (next hops)
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")) and lines[i].strip():
                    block_lines.append(lines[i])
                    i += 1
                # Parse block lines
                parsed = parse_route_block(block_lines)
                result[current_instance][current_af].extend(parsed)
            else:
                i += 1

        return result