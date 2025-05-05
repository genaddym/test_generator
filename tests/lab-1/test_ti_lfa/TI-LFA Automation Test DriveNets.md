# DriveNets TI-LFA Validation Test

1. #### Retrieve ISIS Instance ID

Execute on DUT: `show config protocols isis` command.

- Command output:
```
protocols
  isis
    instance INSTANCE_ID
```

2. #### Validate that TI-LFA is configured under the ISIS INSTANCE_ID.

  1. Execute on DUT: `show config protocols isis instance INSTANCE_ID address-family ipv4-unicast ti-fast-reroute` command.

Check in the command output that it matches below output.

- Command output:
```
protocols
  isis
    instance INSTANCE_ID
      address-family ipv4-unicast
        ti-fast-reroute
          admin-state enabled
          protection-mode link
```

  2. Execute on DUT: `show config protocols isis instance INSTANCE_ID address-family ipv6-unicast ti-fast-reroute` command.

Check in the command output that there is a string illustrated below.

- Command output:
```
protocols
  isis
    instance INSTANCE_ID
      address-family ipv6-unicast
        ti-fast-reroute
          admin-state enabled
          protection-mode link
```

3. #### Retrieve all ISIS enabled interfaces.

  1. Execute on DUT: `show isis interfaces` command.

  Check in the command output that there is a string of `Instance INSTANCE_ID:`.

  Check in the command output that there is a string of `bundle-*`. The `*` after the `bundle-` means that it can be any integer value.

  Save these bundles into a set called `JANUS_ISIS_LINKS`. All individual bundles should use the variable `ISIS_BUNDLE` and it has the following format: bundle-178. Which is `bundle-` following by an integer value.
  
  - Command output:
  ```
  Instance 33287:
                      
  ISIS_BUNDLE                                      
  ```

4. #### Check TI-LFA configuration under each ISIS bundle.
  
  1. Execute on DUT: `show config protocols isis instance 33287 interface ISIS_BUNDLE` command.

  For each `ISIS_BUNDLE` in the `JANUS_ISIS_LINKS` check in the command output that it matches exactly the following:

  - Command output:
  ```
      interface ISIS_BUNDLE
        address-family ipv4-unicast
          fast-reroute backup-candidate disabled
        !
        address-family ipv6-unicast
          fast-reroute backup-candidate disabled
  ```

5. #### Validate in the ISIS INSTANCE_ID operational database that TI-LFA is enabled for IPv4 and IPv6 for link-protection.

  1. Execute on DUT: `show isis instance INSTANCE_ID` command.

Check in the command output that there is a string illustrated below.

- Command output:
```
    TI-LFA:
      IPv4                : enabled, link-protection
      IPv6                : enabled, link-protection
```

6. #### Retrieve random 10 prefixes from the command `show isis route table mpls-sr` for each address family - `ipv4 segment-routing mpls table` and `ipv6 segment-routing mpls table` under the `Prefix` column and save them in the set called `IPV4_ISIS_PREFIXES` and `IPV6_ISIS_PREFIXES`. Each prefix within the corresponding set will be called `IPV4_PREFIX` and `IPV6_PREFIX`.

  1. Execute on DUT: `show isis route table mpls-sr` command.

Check in the command output that there is a string of `ipv4 segment-routing mpls table:`. Under it there is a column `Prefix` which contains the `IPV4_ISIS_PREFIXES`.

Check in the command output that there is a string of `ipv6 segment-routing mpls table:`. Under it there is a column `Prefix` which contains the `IPV6_ISIS_PREFIXES`.


- Command output:
```
ipv4 segment-routing mpls table:
Prefix           
                
IPV4_PREFIX 

ipv6 segment-routing mpls table:

Prefix
IPV6_PREFIX
```

7. #### Validate that there is an alternate path for each prefix in `IPV4_ISIS_PREFIXES` and `IPV6_ISIS_PREFIXES` in the FIB.

  1. Execute on DUT: `show route forwarding-table ipv4 IPV4_PREFIX` command.

Check in the command output that there is a string of `Destination: IPV4_PREFIX`.
Check in the command output that there is a string of `Alternate`.
Check in the command output that there is a string of `next-hop`.
Check in the command output that there is a string of `interface: bundle-*`.

- Command output:
```
Destination: IPV4_PREFIX
    Enhanced-Alternate:
      next-hop
      interface: bundle-*
```

  2. Execute on DUT: `show route forwarding-table ipv6 IPV6_PREFIX` command.

Check in the command output that there is a string of `Destination: IPV6_PREFIX`.
Check in the command output that there is a string of `Alternate`.
Check in the command output that there is a string of `next-hop`.
Check in the command output that there is a string of `interface: bundle-*`.

- Command output:
```
Destination: IPV4_PREFIX
    Enhanced-Alternate:
      next-hop
      interface: bundle-*
```
