import unittest
from decipher import ShowIsisInstanceInstanceIdDecipher

class TestShowIsisInstanceInstanceIdDecipher(unittest.TestCase):
    """
    Unit test for ShowIsisInstanceInstanceIdDecipher class.
    """

    CLI_OUTPUT = (
        "TE Router ID    : 96.109.183.50\r\n"
        "TE Ipv6 Router ID    : 2001:558:4c0:0:3000::50\r\n"
        "Graceful-Restart: disabled\r\n"
        "Graceful-Restart helper-mode   : enabled\r\n"
        "NSR: enabled\r\n"
        "  state: not-ready\r\n"
        "  last recovery: N/A\r\n"
        "Number of areas : 1\r\n"
        "ISIS routes max/threshold/current: 32000/75/368\r\n"
        "ISIS adjacencies max/threshold/current: 500/75/8\r\n"
        "Finger print validation: disabled\r\n"
        "  id: 52c52573-0ef7-4778-9779-8870bcebdbaf\r\n"
        "Instance 33287:\r\n"
        "  Admin state     : enabled\r\n"
        "  System Id       : 0961.0918.3050\r\n"
        "  Area-id(s)      : 49.0000\r\n"
        "  ipv4 level-1 TE Status         : disable\r\n"
        "  ipv4 level-2 TE Status         : enable\r\n"
        "  ipv6 level-1 TE Status         : disable\r\n"
        "  ipv6 level-2 TE Status         : enable\r\n"
        "  Dynamic Hostname          : pcr01.site10.cran1\r\n"
        "  Administrative Distance   : 115\r\n"
        "  ISIS Levels: level-2\r\n"
        "  Segment-Routing MPLS:\r\n"
        "    Ipv4: enabled\r\n"
        "    Ipv6: enabled\r\n"
        "    SRLB: 15000 - 16999\r\n"
        "    SRGB: 400000 - 699999\r\n"
        " Microloop avoidance Ipv4u: enabled, sr-te, fib-delay(remaining): 3000(0)ms, maximum-labels: 3\r\n"
        " Microloop avoidance Ipv6u: enabled, sr-te, fib-delay(remaining): 3000(0)ms, maximum-labels: 3\r\n"
        "  Lsp-flood-reduction: enabled\r\n"
        "  Ignore-attached-bit: disabled\r\n"
        "  Topologies:\r\n"
        "    IPv4 Unicast\r\n"
        "    IPv6 Unicast\r\n"
        "    IPv4 Multicast\r\n"
        "  Load-balancing:\r\n"
        "    IPv4:  max-path: 32, load-balancing-method: ecmp          \r\n"
        "    IPv6:  max-path: 32, load-balancing-method: ecmp          \r\n"
        "  Level-2:\r\n"
        "    IPv4-Unicast topology computation:\r\n"
        "      Last run elapsed  : 00:02:14 ago\r\n"
        "      Last run duration : 3927 usec\r\n"
        "      Run count         : 78344\r\n"
        "      Delay             : 50 msec\r\n"
        "      Min holdtime      : 100 msec\r\n"
        "      Max holdtime      : 2000 msec\r\n"
        "      Next schedule     : N/A\r\n"
        "    Shortcuts IPv4-Unicast topology computation:\r\n"
        "      Last run elapsed  : 00:02:14 ago\r\n"
        "      Last run duration : 1630 usec\r\n"
        "      Run count         : 78344\r\n"
        "      Delay             : 50 msec\r\n"
        "      Min holdtime      : 100 msec          \r\n"
        "      Max holdtime      : 2000 msec\r\n"
        "      Next schedule     : N/A\r\n"
        "    IPv6-Unicast topology computation:\r\n"
        "      Last run elapsed  : 00:02:14 ago\r\n"
        "      Last run duration : 2311 usec\r\n"
        "      Run count         : 78344\r\n"
        "      Delay             : 50 msec\r\n"
        "      Min holdtime      : 100 msec\r\n"
        "      Max holdtime      : 2000 msec\r\n"
        "      Next schedule     : N/A\r\n"
        "    IPv4-Multicast topology computation:\r\n"
        "      Last run elapsed  : 14w4d19h ago\r\n"
        "      Last run duration : 0 usec\r\n"
        "      Run count         : 0\r\n"
        "      Delay             : 0 msec\r\n"
        "      Min holdtime      : 5 msec\r\n"
        "      Max holdtime      : 5000 msec\r\n"
        "      Next schedule     : N/A\r\n"
        "    Max-metric-value             : 16777214\r\n"
        "    IPv4 Unicast default metric  : 10\r\n"
        "    IPv6 Unicast default metric  : 10\r\n"
        "    IPv4 Multicast default metric: 10\r\n"
        "    Overload on-startup: enabled\r\n"
        "      interval: 600\r\n"
        "      wait-for-bgp bgp-delay: 0\r\n"
        "      advertisement-type: overload-bit\r\n"
        "    Overload-bit: off\r\n"
        "    Max-metric: off\r\n"
        "    LSP Throttle:\r\n"
        "      Delay             : 0 msec\r\n"
        "      Min holdtime      : 200 msec\r\n"
        "      Max holdtime      : 2000 msec\r\n"
        "      Next schedule     : 00:35:55.043\r\n"
        "    LSP Lifetime                : 4000 sec\r\n"
        "    LSP Refresh Interval        : 3600 sec\r\n"
        "    LSP Interval                : 0 msec\r\n"
        "    Log Adjacency Changes       : enabled\r\n"
        "    LSP MTU                     : 1492\r\n"
        "    Distribute BGP Link State   : disabled\r\n"
        "    MPLS Traffic Engineering Ipv4 Level-1   : off\r\n"
        "    MPLS Traffic Engineering Ipv4 Level-2   : on\r\n"
        "    MPLS Traffic Engineering Ipv6 Level-1   : off\r\n"
        "    MPLS Traffic Engineering Ipv6 Level-2   : on\r\n"
        "    LFA:\r\n"
        "      IPv4                : disabled\r\n"
        "      IPv6                : disabled\r\n"
        "      IPv4-multicast      : disabled\r\n"
        "    TI-LFA:\r\n"
        "      IPv4                : enabled, link-protection, maximum-labels 3\r\n"
        "      IPv6                : enabled, link-protection, maximum-labels 3"
    )

    def test_decipher_ti_lfa(self):
        decipher = ShowIsisInstanceInstanceIdDecipher()
        result = decipher.decipher(self.CLI_OUTPUT)
        expected = {
            "IPv4": {
                "status": "enabled",
                "link-protection": True,
                "maximum-labels": 3
            },
            "IPv6": {
                "status": "enabled",
                "link-protection": True,
                "maximum-labels": 3
            }
        }
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()