Example of full outputs for the Anycast-SID test:

1. Retrieve Route Policy for IPv4 - DN

asbr01.site10.cran1# show config routing-policy policy IPV4-U-RR-SERVER-OUT

# asbr01.site10.cran1 config-start [12-Apr-2025 21:28:33 UTC]

routing-policy
  policy IPV4-U-RR-SERVER-OUT
    rule 10 deny
      match community BGP-LU-CL
    !
    rule 20 allow
      match ipv4 prefix IPV4-ADS-UET-UEN-PFX
      set ipv4 next-hop 96.109.183.232
    !
    rule 30 allow
      match as-path IS-LOCAL
      set ipv4 next-hop 96.109.183.47
    !
    rule 40 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-RESI-AR-PREFIXES-CL
      set ipv4 next-hop 96.109.183.228
    !
    rule 50 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-AR-PREFIXES-CL
      set ipv4 next-hop 96.109.183.227
    !
    rule 60 allow
      match as-path IBONE-ASPATH
      set ipv4 next-hop 96.109.183.74
    !
    rule 999 deny
    !
  !
!
asbr01.site10.cran1# show as-path-list LEGACY-ASPATH

as-path-list LEGACY-ASPATH
  rule 10 allow regex ^4200001220_
!
asbr01.site10.cran1# show large-community-list LEGACY-RESI-AR-PREFIXES-CL

large-community-list LEGACY-RESI-AR-PREFIXES-CL
  rule 10 allow value 33287:1:901
!
asbr01.site10.cran1# show large-community-list LEGACY-AR-PREFIXES-CL

large-community-list LEGACY-AR-PREFIXES-CL
  rule 10 allow value 33287:1:902
!
as-path-list IBONE-ASPATH
  rule 10 allow regex ^7922_
!

3. Retrieve Route Policy for IPv6 - DN

asbr01.site10.cran1# show config routing-policy policy IPV6-U-RR-SERVER-OUT

# asbr01.site10.cran1 config-start [12-Apr-2025 21:39:08 UTC]

routing-policy
  policy IPV6-U-RR-SERVER-OUT
    rule 10 deny
      match community BGP-LU-CL
    !
    rule 20 allow
      match as-path IS-LOCAL
      set ipv6 next-hop 2001:558:4c0:0:3000::47
    !
    rule 30 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-RESI-AR-PREFIXES-CL
      set ipv6 next-hop 2001:558:4c0:0:3001::30
    !
    rule 40 allow
      match as-path LEGACY-ASPATH
      match large-community LEGACY-AR-PREFIXES-CL
      set ipv6 next-hop 2001:558:4c0:0:3001::20
    !
    rule 50 allow
      match as-path IBONE-ASPATH
      set ipv6 next-hop 2001:558:4c0:0:3001::10
    !
    rule 999 deny
    !
  !
!
asbr01.site10.cran1# show as-path-list LEGACY-ASPATH

as-path-list LEGACY-ASPATH
  rule 10 allow regex ^4200001220_
!
asbr01.site10.cran1# show large-community-list LEGACY-RESI-AR-PREFIXES-CL

large-community-list LEGACY-RESI-AR-PREFIXES-CL
  rule 10 allow value 33287:1:901
!
asbr01.site10.cran1# show large-community-list LEGACY-AR-PREFIXES-CL

large-community-list LEGACY-AR-PREFIXES-CL
  rule 10 allow value 33287:1:902
!
as-path-list IBONE-ASPATH
  rule 10 allow regex ^7922_
!

5. Retrieve Route Policy for IPv4 - Arista

asbr01.site2.cran1#show running-config section IPV4-U-RR-SERVER-OUT
router general
   control-functions
      code unit IPV4-U-RR-SERVER-OUT
         function IPV4_U_RR_SERVER_OUT() {
            if community match community_list BGP-LU-CL {
               return false;
            }
            if prefix match prefix_list_v4 IPV4-ADS-UET-UEN-PFX {
              next_hop = 96.109.183.231;
              return true;
            }
            if as_path match as_path_list IS-LOCAL {
               next_hop = 96.109.183.9;
               return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-RESI-AR-PREFIXES-CL {
               next_hop =  96.109.183.226;
               return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-AR-PREFIXES-CL {
               next_hop = 96.109.183.225;
               return true;
            }
            if as_path match as_path_list IBONE-ASPATH {
               next_hop = 96.109.183.66;
               return true;
            }
         }

asbr01.site2.cran1#show running-config section as-path
ip as-path access-list CBONE-MCAST-ASPATH permit ^23253_3673[2-3]_ any
ip as-path access-list IBONE-ASPATH permit ^7922_ any
ip as-path access-list IBONE-LEARNED-PREFIXES permit ^7922_ any
ip as-path access-list IBONE_ASPATH permit ^7922_ any
ip as-path access-list IBONE_LEARNED_PREFIXES permit ^7922_ any
ip as-path access-list IS-LOCAL permit ^$ any
ip as-path access-list LEGACY-ASPATH permit ^4200001220_ any
ip as-path access-list LEGACY_ASPATH permit ^65001_ any

asbr01.site2.cran1#show running-config section community-list
ip community-list regexp BGP-LU-CL permit .*:1305
ip community-list regexp CDN-CL permit .*:3060
ip community-list regexp CDV-HARMONY-CL permit .*:1077
ip community-list regexp CRAN-CET-CL permit 33287:1060
ip community-list JANUS-LAB-BGP-LU-CL permit 33287:1305
ip community-list JANUS-LAB-CDN-CL permit 33287:3060
ip community-list LEGACY-AR-PREFIXES-CL permit 33287:902
ip community-list LEGACY-AR-PREFIXES-CL permit 65001:902
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 33287:901
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 65001:901
ip community-list LEGACY_AR_PREFIXES_CL permit 33287:902
ip community-list LEGACY_RESI_AR_PREFIXES_CL permit 33287:901
ip community-list regexp PAID-PEER-CL permit .*:3020
ip community-list regexp SFI-CL permit .*:3000
ip community-list regexp SIP-PEER-CL permit .*:3010
ip community-list regexp TRANSIT-CL permit .*:3050
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:302
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:303
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:304
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:305
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:306
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:30[2-6]
ip large-community-list regexp large-community-test permit .*:1305:301

7. Retrieve Route Policy for IPv6 - Arista

asbr01.site2.cran1#show running-config section IPV6-U-RR-SERVER-OUT
router bgp 33287
   neighbor IPV6-U-RR-SERVER route-map IPV6-U-RR-SERVER-OUT out
router general
   control-functions
      code unit IPV6-U-RR-SERVER-OUT
           function IPV6_U_RR_SERVER_OUT() {
            if community match community_list BGP-LU-CL {
             return false;
            }
            if as_path match as_path_list IS-LOCAL {
             next_hop = 2001:558:4c0:0:3000::9;
             return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-RESI-AR-PREFIXES-CL {
             next_hop = 2001:558:4c0:0:3001::32;
             return true;
            }
            if as_path match as_path_list LEGACY-ASPATH and community match community_list LEGACY-AR-PREFIXES-CL {
             next_hop = 2001:558:4c0:0:3001::22;
             return true;
            }
            if as_path match as_path_list IBONE-ASPATH {
             next_hop = 2001:558:4c0:0:3001::2;
             return true;
            }
          return false;
          }

asbr01.site2.cran1#show running-config section as-path
ip as-path access-list CBONE-MCAST-ASPATH permit ^23253_3673[2-3]_ any
ip as-path access-list IBONE-ASPATH permit ^7922_ any
ip as-path access-list IBONE-LEARNED-PREFIXES permit ^7922_ any
ip as-path access-list IBONE_ASPATH permit ^7922_ any
ip as-path access-list IBONE_LEARNED_PREFIXES permit ^7922_ any
ip as-path access-list IS-LOCAL permit ^$ any
ip as-path access-list LEGACY-ASPATH permit ^4200001220_ any
ip as-path access-list LEGACY_ASPATH permit ^65001_ any

asbr01.site2.cran1#show running-config section community-list
ip community-list regexp BGP-LU-CL permit .*:1305
ip community-list regexp CDN-CL permit .*:3060
ip community-list regexp CDV-HARMONY-CL permit .*:1077
ip community-list regexp CRAN-CET-CL permit 33287:1060
ip community-list JANUS-LAB-BGP-LU-CL permit 33287:1305
ip community-list JANUS-LAB-CDN-CL permit 33287:3060
ip community-list LEGACY-AR-PREFIXES-CL permit 33287:902
ip community-list LEGACY-AR-PREFIXES-CL permit 65001:902
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 33287:901
ip community-list LEGACY-RESI-AR-PREFIXES-CL permit 65001:901
ip community-list LEGACY_AR_PREFIXES_CL permit 33287:902
ip community-list LEGACY_RESI_AR_PREFIXES_CL permit 33287:901
ip community-list regexp PAID-PEER-CL permit .*:3020
ip community-list regexp SFI-CL permit .*:3000
ip community-list regexp SIP-PEER-CL permit .*:3010
ip community-list regexp TRANSIT-CL permit .*:3050
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:302
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:303
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:304
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:305
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:306
ip large-community-list regexp NO-EXPORT-LOOPBACK-CL permit .*:1305:30[2-6]
ip large-community-list regexp large-community-test permit .*:1305:301

9. Check the BGP routing table entry for a given PREFIX on DN PCR. 

pcr01.site10.cran1(12-Apr-2025-21:45:43)# show bgp route 11.100.0.0/24

BGP IPv4 Unicast routing table entry for 11.100.0.0/24
Paths: (5 available, best #1, table Default-IP-Routing-Table)
  Not advertised to any peer
 Path #1
  4200001220 150
      96.109.183.228 (metric 2101) from 10.28.88.132 (96.109.183.47)
     Origin IGP, localpref 100, valid, internal, best
     Community: 33287:1050
     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
     Originator: 96.109.183.47, Cluster list: 10.28.88.132 
     AddPath ID: RX 2, TX 3
     Last update: 10-Apr-2025 17:34:27 UTC

 Path #2
  4200001220 150, (stale)
      96.109.183.226 (metric 2441) from 10.28.88.100 (96.109.183.6)
     Origin IGP, localpref 100, valid, internal, alternate-path
     Community: 33287:901 33287:1050
     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
     Originator: 96.109.183.6, Cluster list: 10.28.88.100 
     AddPath ID: RX 2, TX 5
     Last update: 12-Apr-2025 21:26:58 UTC

 Path #3
  4200001220 150
      96.109.183.226 (metric 2441) from 10.28.88.132 (96.109.183.6)
     Origin IGP, localpref 100, valid, internal
     Community: 33287:901 33287:1050
     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
     Originator: 96.109.183.6, Cluster list: 10.28.88.132 
     AddPath ID: RX 3, TX 2
     Last update: 12-Apr-2025 21:17:35 UTC

 Path #4
  4200001220 150, (stale)
      96.109.183.228 (metric 2101) from 10.28.88.100 (96.109.183.47)
     Origin IGP, localpref 100, valid, internal
     Community: 33287:1050
     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
     Originator: 96.109.183.47, Cluster list: 10.28.88.100 
     AddPath ID: RX 3, TX 6
     Last update: 12-Apr-2025 18:22:06 UTC

 Path #5
  4200001220 150, (stale)
      96.109.183.228 (metric 2101) from 10.28.88.100 (96.109.183.47)
     Origin IGP, localpref 100, valid, internal
     Community: 33287:1050
     RPKI best-path selection: enabled, allow-invalid: disabled, prefix-validation state: unverified
     Originator: 96.109.183.47, Cluster list: 10.28.88.100 
     AddPath ID: RX 1, TX 4
     Last update: 12-Apr-2025 17:46:19 UTC

% Network not in IPv4 Multicast table
% Network not in IPv4 Vpn table

pcr01.site10.cran1# 

10. Check the routing table entry for a given PREFIX on DN PCR.

pcr01.site10.cran1# show route 11.100.0.0/24
pcr01.site10.cran1(12-Apr-2025-21:46:50)# show route 11.100.0.0/24

VRF: default
Routing entry for 11.100.0.0/24
  Known via "bgp", priority low, distance 200, metric 0, vrf default, best, fib
  Last update 00:19:51 ago, ack
    96.109.183.228 (recursive)
  *   96.217.0.229, via bundle-178 label 406040
  *   96.217.1.202, via bundle-349 alternate label 406115/406176/3
    96.109.183.226 alternate (recursive)
  *   96.217.0.229, via bundle-178 label 406032
  *   96.217.1.202, via bundle-349 alternate label 406109/3

11. Check the BGP routing table entry for a given PREFIX on Arista PCR.

pcr01.site2.cran1#show ip bgp 11.100.0.0/24
BGP routing table information for VRF default
Router identifier 96.109.183.12, local AS number 33287
BGP routing table entry for 11.100.0.0/24
 Paths: 2 available
  4200001220 150
    96.109.183.226 from 10.28.88.100 (10.28.88.100)
      Origin IGP, metric 0, localpref 100, IGP metric 2151, weight 0, tag 0
      Received 2d04h ago, valid, internal, best
      Originator: 96.109.183.6, Cluster list: 10.28.88.100 
      Community: 33287:901 33287:1050
      Rx path id: 0x2
      Rx SAFI: Unicast
      Tunnel RIB eligible
  4200001220 150
    96.109.183.228 from 10.28.88.100 (10.28.88.100)
      Origin IGP, metric 0, localpref 100, IGP metric 2191, weight 0, tag 0
      Received 00:00:59 ago, valid, internal, backup
      Originator: 96.109.183.47, Cluster list: 10.28.88.100 
      Community: 33287:1050
      Rx path id: 0x3
      Rx SAFI: Unicast
      Tunnel RIB eligible

pcr01.site2.cran1#show ipv6 bgp 2001:558:4c0:464::/64
BGP routing table information for VRF default
Router identifier 96.109.183.12, local AS number 33287
BGP routing table entry for 2001:558:4c0:464::/64
 Paths: 4 available
  4200001220
    2001:558:4c0:0:3001::32 from 2001:558:1047:4007::5 (10.28.88.133)
      Origin INCOMPLETE, metric 0, localpref 100, IGP metric 2151, weight 0, tag 0
      Received 00:00:52 ago, valid, internal, ECMP head, ECMP, best, ECMP contributor
      Originator: 96.109.183.6, Cluster list: 10.28.88.133 
      Community: 33287:901
      Rx path id: 0x3
      Rx SAFI: Unicast
      Tunnel RIB eligible
  4200001220
    2001:558:4c0:0:3001::32 from 2001:558:1047:504::5 (10.28.88.101)
      Origin INCOMPLETE, metric 0, localpref 100, IGP metric 2151, weight 0, tag 0
      Received 00:00:50 ago, valid, internal, ECMP, ECMP contributor
      Originator: 96.109.183.6, Cluster list: 10.28.88.101 10.28.88.133 
      Community: 33287:901
      Rx path id: 0x1
      Rx SAFI: Unicast
      Tunnel RIB eligible
  4200001220
    2001:558:4c0:0:3001::30 from 2001:558:1047:4007::5 (10.28.88.133)
      Origin INCOMPLETE, metric 100, localpref 100, IGP metric 2191, weight 0, tag 0
      Received 00:00:52 ago, valid, internal, backup
      Originator: 96.109.183.47, Cluster list: 10.28.88.133 
      Rx path id: 0x1
      Rx SAFI: Unicast
      Tunnel RIB eligible
  4200001220
    2001:558:4c0:0:3001::30 from 2001:558:1047:504::5 (10.28.88.101)
      Origin INCOMPLETE, metric 100, localpref 100, IGP metric 2191, weight 0, tag 0
      Received 00:01:10 ago, valid, internal
      Originator: 96.109.183.47, Cluster list: 10.28.88.101 
      Rx path id: 0x2
      Rx SAFI: Unicast
      Tunnel RIB eligible

12. Check the routing table entry for a given PREFIX on Arista PCR.

pcr01.site2.cran1#show ipv6 route 2001:558:4c0:464::/64

VRF: default
Routing entry for 2001:558:4c0:464::/64
Source Codes:
       C - connected, S - static, K - kernel, O3 - OSPFv3,
       O3 IA - OSPFv3 inter area, O3 E1 - OSPFv3 external type 1,
       O3 E2 - OSPFv3 external type 2,
       O3 N1 - OSPFv3 NSSA external type 1
       O3 N2 - OSPFv3 NSSA external type2, B - Other BGP Routes,
       A B - BGP Aggregate, R - RIP,
       I L1 - IS-IS level 1, I L2 - IS-IS level 2, DH - DHCP,
       NG - Nexthop Group Static Route, M - Martian,
       DP - Dynamic Policy Route, L - VRF Leaked,
       G  - gRIBI, RC - Route Cache Route,
       CL - CBF Leaked Route

 B I      2001:558:4c0:464::/64 [200/0]
           via 2001:558:4c0:0:3001::32/128, IS-IS SR tunnel index 77
              via fe80::3a38:a6ff:fea5:9943, Port-Channel127, label 606032
              via fe80::3a38:a6ff:fea5:adb9, Port-Channel112, label 606032
           via 2001:558:4c0:0:3001::30/128, IS-IS SR tunnel index 36, backup
              via TI-LFA tunnel index 5, label 606040
                 via fe80::3a38:a6ff:fea5:adb9, Port-Channel112, label imp-null(3)
                 backup via fe80::3a38:a6ff:fea5:9943, Port-Channel127, label imp-null(3)
