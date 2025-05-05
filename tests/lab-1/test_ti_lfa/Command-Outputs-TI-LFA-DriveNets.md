# Example of full outputs for the TI-LFA test for DriveNets:

1. Retrieve ISIS Instance ID

pcr01.site10.cran1(13-Apr-2025-19:16:58)# show config protocols isis

# pcr01.site10.cran1 config-start [13-Apr-2025 19:16:58 UTC]

protocols
  isis
    maximum-adjacencies 500 threshold 75
    maximum-routes 1000000 threshold 75
    nsr enabled
    instance 33287
      advertise overload-bit disabled
      authentication level level-2 snp-auth sign-validate
      authentication level level-2 type md5 password enc-gAAAAABjXXXJlaMZt7SYQ5uMfhR_e18iH5__zx1yTt-w3HqCDO1DTr-n6_JtgtIBIW9NslQ6GVdhF6x9ZbAGHibxnovvS3fa2g==
      dynamic-hostname enabled
      iso-network 49.0000.0961.0918.3050.00
      level level-2
      lsp-mtu 1492
      max-metric 16777214
      address-family ipv4-unicast
        maximum-paths 32
        prefix-priority high tag 5
        traffic-engineering level level-2 enabled
        microloop-avoidance
          admin-state enabled
          fib-delay 3000
        !
        segment-routing
          admin-state enabled
        !
        ti-fast-reroute
          admin-state enabled
          protection-mode link
        !
        timers
          throttle spf delay 50 max-holdtime 2000 min-holdtime 100
        !
      !
      address-family ipv6-unicast
        maximum-paths 32
        prefix-priority high tag 5
        topology enabled
        traffic-engineering level level-2 enabled
        microloop-avoidance
          admin-state enabled
          fib-delay 3000
        !
        segment-routing
          admin-state enabled
        !
        ti-fast-reroute
          admin-state enabled
          protection-mode link
        !
        timers
          throttle spf delay 50 max-holdtime 2000 min-holdtime 100
        !
      !                                     
      flex-algo
        use-legacy-te disabled
        participate 128
        !
      !

2. show config protocols isis instance 33287 address-family ipv4-unicast ti-fast-reroute

pcr01.site10.cran1(13-Apr-2025-19:17:54)# show config protocols isis instance 33287 address-family ipv4-unicast ti-fast-reroute

# pcr01.site10.cran1 config-start [13-Apr-2025 19:17:54 UTC]

protocols
  isis
    instance 33287
      address-family ipv4-unicast
        ti-fast-reroute
          admin-state enabled
          protection-mode link
        !
      !
    !
  !
!

3. #### Retrieve all ISIS enabled interfaces.

  1. show isis interfaces

  pcr01.site10.cran1(22-Apr-2025-15:18:33)# show isis interfaces 

  Instance 33287:
    Interface                                          State    Type           Level
    bundle-178                                         Up       point-to-point L2       
    bundle-247                                         Up       point-to-point L2       
    bundle-349                                         Up       point-to-point L2       
    bundle-352                                         Up       point-to-point L2       
    bundle-355                                         Up       point-to-point L2       
    bundle-742                                         Up       point-to-point L2       
    bundle-745                                         Up       point-to-point L2       

4. #### Check TI-LFA configuration under each ISIS bundle.

  1. show config protocols isis instance 33287 interface bundle-178

protocols
  isis
    instance 33287
      interface bundle-178
        authentication md5 password enc-gAAAAABjXXXJlaMZt7SYQ5uMfhR_e18iH5__zx1yTt-w3HqCDO1DTr-n6_JtgtIBIW9NslQ6GVdhF6x9ZbAGHibxnovvS3fa2g==
        level level-2
        network-type point-to-point
        address-family ipv4-unicast
          fast-reroute backup-candidate enabled
          metric level level-2 2000
        !
        address-family ipv6-unicast
          fast-reroute backup-candidate enabled
          metric level level-2 2000
        !
        delay-normalization
          interval 10
          offset 0
        !
      !
    !
  !
!


5. #### Validate in the ISIS INSTANCE_ID operational database that TI-LFA is enabled for IPv4 and IPv6 for link-protection.

show isis instance 33287

pcr01.site10.cran1(13-Apr-2025-19:18:47)# show isis instance 33287 

TE Router ID    : 96.109.183.50
TE Ipv6 Router ID    : 2001:558:4c0:0:3000::50
Graceful-Restart: disabled
Graceful-Restart helper-mode   : enabled
NSR: enabled
  state: not-ready
  last recovery: N/A
Number of areas : 1
ISIS routes max/threshold/current: 32000/75/368
ISIS adjacencies max/threshold/current: 500/75/8
Finger print validation: disabled
  id: 52c52573-0ef7-4778-9779-8870bcebdbaf
Instance 33287:
  Admin state     : enabled
  System Id       : 0961.0918.3050
  Area-id(s)      : 49.0000
  ipv4 level-1 TE Status         : disable
  ipv4 level-2 TE Status         : enable
  ipv6 level-1 TE Status         : disable
  ipv6 level-2 TE Status         : enable
  Dynamic Hostname          : pcr01.site10.cran1
  Administrative Distance   : 115
  ISIS Levels: level-2
  Segment-Routing MPLS:
    Ipv4: enabled
    Ipv6: enabled
    SRLB: 15000 - 16999
    SRGB: 400000 - 699999
 Microloop avoidance Ipv4u: enabled, sr-te, fib-delay(remaining): 3000(0)ms, maximum-labels: 3
 Microloop avoidance Ipv6u: enabled, sr-te, fib-delay(remaining): 3000(0)ms, maximum-labels: 3
  Lsp-flood-reduction: enabled
  Ignore-attached-bit: disabled
  Topologies:
    IPv4 Unicast
    IPv6 Unicast
    IPv4 Multicast
  Load-balancing:
    IPv4:  max-path: 32, load-balancing-method: ecmp          
    IPv6:  max-path: 32, load-balancing-method: ecmp          
  Level-2:
    IPv4-Unicast topology computation:
      Last run elapsed  : 00:02:14 ago
      Last run duration : 3927 usec
      Run count         : 78344
      Delay             : 50 msec
      Min holdtime      : 100 msec
      Max holdtime      : 2000 msec
      Next schedule     : N/A
    Shortcuts IPv4-Unicast topology computation:
      Last run elapsed  : 00:02:14 ago
      Last run duration : 1630 usec
      Run count         : 78344
      Delay             : 50 msec
      Min holdtime      : 100 msec          
      Max holdtime      : 2000 msec
      Next schedule     : N/A
    IPv6-Unicast topology computation:
      Last run elapsed  : 00:02:14 ago
      Last run duration : 2311 usec
      Run count         : 78344
      Delay             : 50 msec
      Min holdtime      : 100 msec
      Max holdtime      : 2000 msec
      Next schedule     : N/A
    IPv4-Multicast topology computation:
      Last run elapsed  : 14w4d19h ago
      Last run duration : 0 usec
      Run count         : 0
      Delay             : 0 msec
      Min holdtime      : 5 msec
      Max holdtime      : 5000 msec
      Next schedule     : N/A
    Max-metric-value             : 16777214
    IPv4 Unicast default metric  : 10
    IPv6 Unicast default metric  : 10
    IPv4 Multicast default metric: 10
    Overload on-startup: enabled
      interval: 600
      wait-for-bgp bgp-delay: 0
      advertisement-type: overload-bit
    Overload-bit: off
    Max-metric: off
    LSP Throttle:
      Delay             : 0 msec
      Min holdtime      : 200 msec
      Max holdtime      : 2000 msec
      Next schedule     : 00:35:55.043
    LSP Lifetime                : 4000 sec
    LSP Refresh Interval        : 3600 sec
    LSP Interval                : 0 msec
    Log Adjacency Changes       : enabled
    LSP MTU                     : 1492
    Distribute BGP Link State   : disabled
    MPLS Traffic Engineering Ipv4 Level-1   : off
    MPLS Traffic Engineering Ipv4 Level-2   : on
    MPLS Traffic Engineering Ipv6 Level-1   : off
    MPLS Traffic Engineering Ipv6 Level-2   : on
    LFA:
      IPv4                : disabled
      IPv6                : disabled
      IPv4-multicast      : disabled
    TI-LFA:
      IPv4                : enabled, link-protection, maximum-labels 3
      IPv6                : enabled, link-protection, maximum-labels 3

6. #### Retrieve random 10 prefixes from the command `show isis route table mpls-sr` for each address family - `ipv4 segment-routing mpls table` and `ipv6 segment-routing mpls table` under the `Prefix` column and save them in the set called `IPV4_ISIS_PREFIXES` and `IPV6_ISIS_PREFIXES`. Each prefix within the corresponding set will be called `IPV4_PREFIX` and `IPV6_PREFIX`.
 
show isis route table mpls-sr

pcr01.site10.cran1(13-Apr-2025-19:19:46)#  show isis route table mpls-sr

Legend: lp - link-protecting LFA, np - node-protecting LFA, 
        lsp - link-srlg-protecting LFA, nsp - node-srlg-protecting LFA, 
        L - ldp-stitching, ul - microloop-avoidance
  Instance 33287
ipv4 segment-routing mpls table:
  Level - 1


  Instance 33287
ipv4 segment-routing mpls table:
  Level - 2
  Destination         Prefix              algorithm    cost      tag           priority         nh-address                 interface           interface-weight    egress-label     Nexthop-srgb-base 
  260                                     spf          2000      Untagged      Low              96.217.0.229               bundle-178          N/A                                  0                 
                                                       12092     Untagged      Low              96.217.1.202 (lp)          bundle-349          N/A                 406115 406151    400000            
  261                                     spf          2000      Untagged      Low              96.217.0.229               bundle-178          N/A                                  0                 
  272                                     spf          40000     Untagged      Low              96.217.1.66                bundle-247          N/A                                  0                 
                                                       4426      Untagged      Low              96.217.0.229 (lp)          bundle-178          N/A                 406248           400000            
  273                                     spf          40000     Untagged      Low              96.217.1.66                bundle-247          N/A                                  0                 
  280                                     spf          5000      Untagged      Low              96.217.1.202               bundle-349          N/A                                  0                 
                                                       9292      Untagged      Low              96.217.0.229 (lp)          bundle-178          N/A                 406127 406138    400000            
  281                                     spf          5000      Untagged      Low              96.217.1.202               bundle-349          N/A                                  0                 
  284                                     spf          2000      Untagged      Low              96.217.1.205               bundle-352          N/A                                  0                 
                                                       16779234  Untagged      Low              96.217.0.229 (lp)          bundle-178          N/A                 406152           400000            
  285                                     spf          2000      Untagged      Low              96.217.1.205               bundle-352          N/A                                  0                 
  288                                     spf          20000     Untagged      Low              96.217.1.210               bundle-355          N/A                                  0                 
                                                       24001     Untagged      Low              96.217.0.229 (lp)          bundle-178          N/A                 406154 406157    400000            
  289                                     spf          20000     Untagged      Low              96.217.1.210               bundle-355          N/A                                  0                 
  292                                     spf          65000     Untagged      Low              96.216.62.242              ge100-0/0/2/2.10    N/A                                  0                 
  293                                     spf          65000     Untagged      Low              96.216.62.242              ge100-0/0/2/2.10    N/A                                  0                 
  626                                     spf          45000     Untagged      Low              96.217.3.210               bundle-745          N/A                                  0                 
  627                                     spf          45000     Untagged      Low              96.217.3.210               bundle-745          N/A                                  0                 
  630                                     spf          45000     Untagged      Low              96.217.3.214               bundle-742          N/A                                  0                 
  631                                     spf          45000     Untagged      Low              96.217.3.214               bundle-742          N/A                                  0                 
  406017              96.109.183.225/32   spf          2441      5             High             96.217.0.229               bundle-178          N/A                 406017           400000            
                                                       12152     5             High             96.217.1.202 (np)          bundle-349          N/A                 406109 3         400000            
  406025              96.109.183.227/32   spf          2101      5             High             96.217.0.229               bundle-178          N/A                 406025           400000            
                                                       12192     5             High             96.217.1.202 (lp)          bundle-349          N/A                 406115 406176 3  400000            
  406032              96.109.183.226/32   spf          2441      5             High             96.217.0.229               bundle-178          N/A                 406032           400000            
                                                       12152     5             High             96.217.1.202 (np)          bundle-349          N/A                 406109 3         400000            
  406040              96.109.183.228/32   spf          2101      5             High             96.217.0.229               bundle-178          N/A                 406040           400000            
                                                       12192     5             High             96.217.1.202 (lp)          bundle-349          N/A                 406115 406176 3  400000            
  406075              96.109.183.227/32   128          31        Untagged      Medium           96.217.0.229               bundle-178          N/A                 406075           400000            
                                                       73        Untagged      Medium           96.217.1.202 (lp)          bundle-349          N/A                 406639 406075    400000            
  406090              96.109.183.228/32   128          31        Untagged      Medium           96.217.0.229               bundle-178          N/A                 406090           400000            
                                                       73        Untagged      Medium           96.217.1.202 (lp)          bundle-349          N/A                 406639 406090    400000            
  406104              96.109.183.1/32     spf          2126      5             High             96.217.0.229               bundle-178          N/A                 406104           400000            
                                                       12152     5             High             96.217.1.202 (np)          bundle-349          N/A                 406115 406104    400000            
  406107              96.109.183.4/32     spf          2026      5             High             96.217.0.229               bundle-178          N/A                 406107           400000            
                                                       12077     5             High             96.217.1.202 (np)          bundle-349          N/A                 406115 406107    400000            
  406108              96.109.183.5/32     spf          2226      5             High             96.217.0.229               bundle-178          N/A                 406108           400000            
                                                       12052     5             High             96.217.1.202 (np)          bundle-349          N/A                 406108           400000            
  406109              96.109.183.6/32     spf          2441      5             High             96.217.0.229               bundle-178          N/A                 406109           400000            
                                                       12152     5             High             96.217.1.202 (np)          bundle-349          N/A                 406109           400000            

ipv6 segment-routing mpls table:
  Level - 2
  Destination         Prefix              algorithm    cost      tag           priority         nh-address                      interface           interface-weight    egress-label   Nexthop-srgb-base 
  262                                     spf          2000      Untagged      Low              fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                                0                 
                                                       12092     Untagged      Low              fe80::8640:76ff:feba:2e0d (lp)  bundle-349          N/A                 606115 606151  400000            
  263                                     spf          2000      Untagged      Low              fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                                0                 
  274                                     spf          40000     Untagged      Low              fe80::e6f2:7cff:fec0:844d       bundle-247          N/A                                0                 
  275                                     spf          40000     Untagged      Low              fe80::e6f2:7cff:fec0:844d       bundle-247          N/A                                0                 
  282                                     spf          5000      Untagged      Low              fe80::8640:76ff:feba:2e0d       bundle-349          N/A                                0                 
                                                       9292      Untagged      Low              fe80::8640:76ff:fe3b:39ed (lp)  bundle-178          N/A                 606127 606138  400000            
  283                                     spf          5000      Untagged      Low              fe80::8640:76ff:feba:2e0d       bundle-349          N/A                                0                 
  286                                     spf          2000      Untagged      Low              fe80::8640:76ff:fe1e:e5cb       bundle-352          N/A                                0                 
                                                       16779234  Untagged      Low              fe80::8640:76ff:fe3b:39ed (lp)  bundle-178          N/A                 606152         400000            
  287                                     spf          2000      Untagged      Low              fe80::8640:76ff:fe1e:e5cb       bundle-352          N/A                                0                 
  290                                     spf          20000     Untagged      Low              fe80::1a5b:ff:fea1:f92d         bundle-355          N/A                                0                 
                                                       24001     Untagged      Low              fe80::8640:76ff:fe3b:39ed (lp)  bundle-178          N/A                 606154 606157  400000            
  291                                     spf          20000     Untagged      Low              fe80::1a5b:ff:fea1:f92d         bundle-355          N/A                                0                 
  294                                     spf          65000     Untagged      Low              fe80::216:1ff:fe00:1            ge100-0/0/2/2.10    N/A                                0                 
  295                                     spf          65000     Untagged      Low              fe80::216:1ff:fe00:1            ge100-0/0/2/2.10    N/A                                0                 
  628                                     spf          45000     Untagged      Low              fe80::2a99:3aff:fea6:7a21       bundle-745          N/A                                0                 
  629                                              spf          45000     Untagged      Low              fe80::2a99:3aff:fea6:7a21       bundle-745          N/A                                  0                 
  632                                              spf          45000     Untagged      Low              fe80::9a5d:82ff:fe96:b69f       bundle-742          N/A                                  0                 
  633                                              spf          45000     Untagged      Low              fe80::9a5d:82ff:fe96:b69f       bundle-742          N/A                                  0                 
  606017              2001:558:4c0:0:3001::22/128  spf          2441      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606017           400000            
                                                                12152     5             High             fe80::8640:76ff:feba:2e0d (np)  bundle-349          N/A                 606109 3         400000            
  606025              2001:558:4c0:0:3001::20/128  spf          2101      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606025           400000            
                                                                12192     5             High             fe80::8640:76ff:feba:2e0d (lp)  bundle-349          N/A                 606115 606176 3  400000            
  606032              2001:558:4c0:0:3001::32/128  spf          2441      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606032           400000            
                                                                12152     5             High             fe80::8640:76ff:feba:2e0d (np)  bundle-349          N/A                 606109 3         400000            
  606040              2001:558:4c0:0:3001::30/128  spf          2101      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606040           400000            
                                                                12192     5             High             fe80::8640:76ff:feba:2e0d (lp)  bundle-349          N/A                 606115 606176 3  400000            
  606075              2001:558:4c0:0:3001::20/128  128          31        Untagged      Medium           fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606075           400000            
                                                                73        Untagged      Medium           fe80::8640:76ff:feba:2e0d (lp)  bundle-349          N/A                 606639 606075    400000            
  606090              2001:558:4c0:0:3001::30/128  128          31        Untagged      Medium           fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606090           400000            
                                                                73        Untagged      Medium           fe80::8640:76ff:feba:2e0d (lp)  bundle-349          N/A                 606639 606090    400000            
  606104              2001:558:4c0:0:3000::1/128   spf          2126      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606104           400000            
                                                                12152     5             High             fe80::8640:76ff:feba:2e0d (np)  bundle-349          N/A                 606115 606104    400000            
  606107              2001:558:4c0:0:3000::4/128   spf          2026      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606107           400000            
                                                                12077     5             High             fe80::8640:76ff:feba:2e0d (np)  bundle-349          N/A                 606115 606107    400000            
  606108              2001:558:4c0:0:3000::5/128   spf          2226      5             High             fe80::8640:76ff:fe3b:39ed       bundle-178          N/A                 606108           400000            
                                                                12052     5             High             fe80::8640:76ff:feba:2e0d (np)  bundle-349          N/A                 606108           400000                        


7. #### Validate that there is an alternate path for each prefix in `IPV4_ISIS_PREFIXES` and `IPV6_ISIS_PREFIXES` in the FIB.

  1. show route forwarding-table ipv4 96.109.183.86/32

pcr01.site10.cran1(13-Apr-2025-19:20:28)# show route forwarding-table ipv4 96.109.183.86/32

NCP-ID: 0
VRF: default
IPv4 Forwarding Table:
Destination: 96.109.183.86/32
    next-hop(1): 96.217.0.229 Active
    interface: bundle-178
    Enhanced-Alternate:
      next-hop: 96.217.1.202
      interface: bundle-349

  2. show route forwarding-table ipv6 2001:558:4c0:0:3000::62/128

pcr01.site10.cran1(13-Apr-2025-19:20:59)# show route forwarding-table ipv6 2001:558:4c0:0:3000::62/128

NCP-ID: 0
VRF: default
IPv6 Forwarding Table:
Destination: 2001:558:4c0:0:3000::62/128
    next-hop(1): fe80::8640:76ff:fe3b:39ed Active
    interface: bundle-178
    Enhanced-Alternate:
      next-hop: fe80::8640:76ff:feba:2e0d
      interface: bundle-349
