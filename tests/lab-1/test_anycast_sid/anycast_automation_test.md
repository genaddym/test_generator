# Anycast-SID Validation

# DriveNets Anycast-SID Policy Extraction (Site10) IPv4

## 1. Retrieve Route Policy for IPv4

Execute on DN ASBR: `show config routing-policy policy IPV4-U-RR-SERVER-OUT` command.

- Command output:
```
routing-policy
  policy IPV4-U-RR-SERVER-OUT
    rule 40 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-RESI-AR-PREFIXES-CL
      set ipv4 next-hop RESI_AR_NH
    ...
    rule 50 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-AR-PREFIXES-CL
      set ipv4 next-hop AR_NH
    ...
    rule 60 allow
      match as-path IBONE-ASPATH
      set ipv4 next-hop IBONE_NH
```

Execute on DN ASBR: `show as-path-list LEGACY-ASPATH` command.

- Command output:
```
as-path-list LEGACY-ASPATH
  rule 10 allow regex ^4200001220_
```

Execute on DN ASBR: `show large-community-list LEGACY-RESI-AR-PREFIXES-CL` command.

- Command output:
```
large-community-list LEGACY-RESI-AR-PREFIXES-CL
  rule 10 allow value 33287:1:901
```

Execute on DN ASBR: `show large-community-list LEGACY-AR-PREFIXES-CL` command.

- Command output:
```
large-community-list LEGACY-AR-PREFIXES-CL
  rule 10 allow value 33287:1:902
```

Execute on DN ASBR: `show as-path-list IBONE-ASPATH` command.

- Command output:
```
as-path-list IBONE-ASPATH
  rule 10 allow regex ^7922_
```

## 2. Based on the previous outputs, create the mapping which correlates the AS-PATH and Large-Communities to the corresponding BGP Next-Hop - `RESI_AR_NH`, `AR_NH`, `IBONE_NH`. Save this mapping into a set called DN_ANYCAST_NEXTHOPS_V4.

```bash
[
  {
    "rule_number": 40,
    "as_path_regex": "^4200001220_",
    "large_community": "33287:1:901",
    "next_hop": "RESI_AR_NH"
  },
  {
    "rule_number": 50,
    "as_path_regex": "^4200001220_",
    "large_community": "33287:1:902",
    "next_hop": "AR_NH"
  },
  {
    "rule_number": 60,
    "as_path_regex": "^7922_",
    "large_community": null,
    "next_hop": "IBONE_NH"
  }
]
```

# DriveNets Anycast-SID Policy Extraction (Site10) IPv6

## 3. Retrieve Route Policy for IPv6

Execute on DN ASBR: `show config routing-policy policy IPV6-U-RR-SERVER-OUT` command.

- Command output:
```
routing-policy
  policy IPV6-U-RR-SERVER-OUT
    rule 30 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-RESI-AR-PREFIXES-CL
      set ipv6 next-hop RESI_AR_NH
    ...
    rule 40 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-AR-PREFIXES-CL
      set ipv6 next-hop AR_NH
    ...
    rule 50 allow
      match as-path IBONE-ASPATH
      set ipv6 next-hop IBONE_NH
```

Execute on DN ASBR: `show as-path-list LEGACY-ASPATH` command.

- Command output:
```
as-path-list LEGACY-ASPATH
  rule 10 allow regex ^4200001220_
```

Execute on DN ASBR: `show large-community-list LEGACY-RESI-AR-PREFIXES-CL` command.

- Command output:
```
large-community-list LEGACY-RESI-AR-PREFIXES-CL
  rule 10 allow value 33287:1:901
```

Execute on DN ASBR: `show large-community-list LEGACY-AR-PREFIXES-CL` command.

- Command output:
```
large-community-list LEGACY-AR-PREFIXES-CL
  rule 10 allow value 33287:1:902
```

Execute on DN ASBR: `show as-path-list IBONE-ASPATH` command.

- Command output:
```
as-path-list IBONE-ASPATH
  rule 10 allow regex ^7922_
```

## 4. Based on the previous outputs, create the mapping which correlates the AS-PATH and Large-Communities to the corresponding BGP Next-Hop - `RESI_AR_NH`, `AR_NH`, `IBONE_NH`.. Save this mapping into a set called DN_ANYCAST_NEXTHOPS_V6.

```bash
[
  {
    "rule_number": 30,
    "as_path_regex": "^4200001220_",
    "large_community": "33287:1:901",
    "next_hop_v6": "RESI_AR_NH"
  },
  {
    "rule_number": 40,
    "as_path_regex": "^4200001220_",
    "large_community": "33287:1:902",
    "next_hop_v6": "AR_NH"
  },
  {
    "rule_number": 50,
    "as_path_regex": "^7922_",
    "large_community": null,
    "next_hop_v6": "IBONE_NH"
  }
]
```

# Arista Anycast-SID Policy Extraction (Site2) - IPv4

## 5. Retrieve Route Policy for IPv4

Execute on DN ASBR: `show running-config section IPV4-U-RR-SERVER-OUT` command.

- Command output:
```
router general
   control-functions
      code unit IPV4-U-RR-SERVER-OUT
         function IPV4_U_RR_SERVER_OUT() {
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-RESI-AR-PREFIXES-CL {
               next_hop = RESI_AR_NH;
               return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-AR-PREFIXES-CL {
               next_hop = AR_NH;
               return true;
            }
            if as_path match as_path_list IBONE-ASPATH {
               next_hop = IBONE_NH;
               return true;
            }
         }
```

Execute on DN ASBR: `show running-config section as-path` command.

- Command output:
```
ip as-path access-list IS-LOCAL permit ^$
ip as-path access-list LEGACY-ASPATH permit ^4200001220_ any
ip as-path access-list IBONE-ASPATH permit ^7922_ any
```

Execute on Arista ASBR: `show running-config section community-list` command.

- Command output:
```
ip community-list LEGACY-AR-PREFIXES-CL permit 33287:902
ip community-list LEGACY-AR-PREFIXES-CL permit 65001:902
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 33287:901
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 65001:901
```

## 6. Based on the previous outputs, create the mapping which correlates the AS-PATH and Large-Communities to the corresponding BGP Next-Hop - `RESI_AR_NH`, `AR_NH`, `IBONE_NH`. Save this mapping into a set called ARISTA_ANYCAST_NEXTHOPS_V4.

```bash
[
  {
    "rule": "LEGACY-RESI-AR",
    "as_path_regex": "^4200001220_",
    "community_match": "33287:901 (or 65001:901)",
    "next_hop_v4": "RESI_AR_NH"
  },
  {
    "rule": "LEGACY-AR",
    "as_path_regex": "^4200001220_",
    "community_match": "33287:902 (or 65001:902)",
    "next_hop_v4": "AR_NH"
  },
  {
    "rule": "IBONE-ASPATH",
    "as_path_regex": "^7922_",
    "community_match": null,
    "next_hop_v4": "IBONE_NH"
  }
]
```

# Arista Anycast-SID Policy Extraction (Site2) - IPv6

## 7. Retrieve Route Policy for IPv6

Execute on Arista ASBR: `show running-config section IPV6-U-RR-SERVER-OUT` command.

- Command output:
```
router general
   control-functions
      code unit IPV6-U-RR-SERVER-OUT
         function IPV6_U_RR_SERVER_OUT() {
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-RESI-AR-PREFIXES-CL {
               next_hop = RESI_AR_NH;
               return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-AR-PREFIXES-CL {
               next_hop = AR_NH;
               return true;
            }
            if as_path match as_path_list IBONE-ASPATH {
               next_hop = IBONE_NH;
               return true;
            }
         }
```

Execute on DN ASBR: `show running-config section as-path` command.

- Command output:
```
ip as-path access-list IS-LOCAL permit ^$
ip as-path access-list LEGACY-ASPATH permit ^4200001220_ any
ip as-path access-list IBONE-ASPATH permit ^7922_ any
```

Execute on DN ASBR: `show running-config section community-list` command.

- Command output:
```
ip community-list LEGACY-AR-PREFIXES-CL permit 33287:902
ip community-list LEGACY-AR-PREFIXES-CL permit 65001:902
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 33287:901
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 65001:901
```

## 8. Based on the previous outputs, create the mapping which correlates the AS-PATH and Large-Communities to the corresponding BGP Next-Hop - `RESI_AR_NH`, `AR_NH`, `IBONE_NH`. Save this mapping into a set called ARISTA_ANYCAST_NEXTHOPS_V6.

```bash
[
  {
    "rule": "LEGACY-RESI-AR",
    "as_path_regex": "^4200001220_",
    "community_match": "33287:901 (or 65001:901)",
    "next_hop_v6": "RESI_AR_NH"
  },
  {
    "rule": "LEGACY-AR",
    "as_path_regex": "^4200001220_",
    "community_match": "33287:902 (or 65001:902)",
    "next_hop_v6": "AR_NH"
  },
  {
    "rule": "IBONE-ASPATH",
    "as_path_regex": "^7922_",
    "community_match": null,
    "next_hop_v6": "IBONE_NH"
  }
]
```
# PCR Anycast BGP Next-Hop Validation DriveNets

## 9. Check the BGP routing table entry for a given PREFIX on DN PCR. 

Check in the command output that there is a string of `BGP IPv4 Unicast routing table entry for PREFIX` for IPv4 or `BGP IPv6 Unicast routing table entry for PREFIX` for IPv6. 

Check in the command output that there is a string of the AS-PATH `4200001220 150`. 

Check in the command output that there is a string of the Next-Hop `96.109.183.228 (metric 2101) from 10.28.88.100 (96.109.183.47)` the first IPv4/IPv6 address is the BGP Next-Hop. 

Check in the command output that there is a string of the Large Community in `Large Community: 33287:1:901`. 

Check this for Path #1 and Path#2. 

Path #1 should have the `best` keyword in the line `Origin IGP, localpref 100, valid, internal, best`. 

Path #2 should have the `alternate-path` in the line `Origin IGP, localpref 100, valid, internal, alternate-path`. 

Compare the BGP Next-Hop with `ARISTA_ANYCAST_NEXTHOPS_V6`, `ARISTA_ANYCAST_NEXTHOPS_V4`, `DN_ANYCAST_NEXTHOPS_V6`, `DN_ANYCAST_NEXTHOPS_V4` sets and validate whether the correct BGP Next-Hop is present, based on the mappings within these sets.

Execute on DN PCR: `show bgp route PREFIX` command. 

- Command output:
```
BGP IPv4 Unicast routing table entry for 11.100.0.0/24
 Path #1
  4200001220 150
      96.109.183.228 (metric 2101) from 10.28.88.100 (96.109.183.47)
     Origin IGP, localpref 100, valid, internal, best 
     Community: 33287:1050
     Large Community: 33287:1:901

 Path #2
  4200001220 150
      96.109.183.226 (metric 2441) from 10.28.88.100 (96.109.183.6)
     Origin IGP, localpref 100, valid, internal, alternate-path
     Community: 33287:901 33287:1050
```

## 10. Check the routing table entry for a given PREFIX on DN PCR.

Execute on DN PCR: `sh route PREFIX` command.

Check in the command output that there is a string of `Routing entry for 11.100.0.0/24`.

Check in the command output that there is a string of `Known via "bgp"`, and `best, fib`.

Check in the command output that there are 2 BGP Next-Hops according the previous output of `show bgp route PREFIX`.

- Command output:
```
Routing entry for 11.100.0.0/24
  Known via "bgp", priority low, distance 200, metric 0, vrf default, best, fib
    96.109.183.228 (recursive)

    96.109.183.226 alternate (recursive)
```

# PCR Anycast BGP Next-Hop Validation Arista

## 11. Check the BGP routing table entry for a given PREFIX on Arista PCR. 

In this output, verify that this is the correct BGP entry for a given PREFIX which is in this line `BGP routing table entry for PREFIX`.

Next check in the command output that there is a string of the AS-PATH `4200001220 150`. 

Next check in the command output that there is a string of the the Next-Hop `96.109.183.226 from 10.28.88.100 (10.28.88.100)` the first IPv4/IPv6 address is the BGP Next-Hop. 

Next check in the command output that there is a string of the Community in `Community: 33287:901 33287:1050`. 

Check this for Path #1 and Path#2. 

Path #1 should have the `best` keyword in the line `Received 1d23h ago, valid, internal, best`. 

Path #2 should have the `backup` in the line `Received 00:00:01 ago, valid, internal, backup`. 

Compare the BGP Next-Hop with `ARISTA_ANYCAST_NEXTHOPS_V6`, `ARISTA_ANYCAST_NEXTHOPS_V4`, `DN_ANYCAST_NEXTHOPS_V6`, `DN_ANYCAST_NEXTHOPS_V4` sets and validate whether the correct BGP Next-Hop is present, based on the mappings within these sets.

Execute on Arista PCR: `show ip bgp PREFIX` command for IPv4 and `show ipv6 bgp PREFIX` command for IPv6. 

- Command output:
```
BGP routing table entry for 11.100.0.0/24
  4200001220 150
    96.109.183.226 from 10.28.88.100 (10.28.88.100)
      Received 1d23h ago, valid, internal, best
      Community: 33287:901 33287:1050
  4200001220 150
    96.109.183.228 from 10.28.88.100 (10.28.88.100)
      Received 00:00:01 ago, valid, internal, backup
      Community: 33287:1050
```

## 12. Check the routing table entry for a given PREFIX on Arista PCR.

Execute on DN PCR: `show ip route PREFIX` command for IPv4 and `show ipv6 route PREFIX` command for IPv6.

Check in the command output that there is a string of `B I      PREFIX [200/0]`.

Check in the command output that there is a string of `via 96.109.183.226/32`.

Check in the command output that there is a string of `via 96.109.183.228/32`.

Check in the command output that there are 2 BGP Next-Hops according the previous output of `show bgp route PREFIX`.

- Command output:
```
 B I      11.100.0.0/24 [200/0]
           via 96.109.183.226/32, IS-IS SR tunnel index 73
           via 96.109.183.228/32, IS-IS SR tunnel index 16, backup
```