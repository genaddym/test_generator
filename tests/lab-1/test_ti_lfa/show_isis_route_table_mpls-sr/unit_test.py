import unittest
from decipher import ShowIsisRouteTableMplssrDecipher

class TestShowIsisRouteTableMplssrDecipher(unittest.TestCase):
    """
    Unit test for ShowIsisRouteTableMpls-srDecipher class.
    """

    CLI_OUTPUT = """Legend: lp - link-protecting LFA, np - node-protecting LFA, 
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
"""

    def test_decipher(self):
        decipher = ShowIsisRouteTableMplssrDecipher()
        parsed = decipher.decipher(self.CLI_OUTPUT)

        # Basic checks
        self.assertIn("33287", parsed)
        instance_data = parsed["33287"]
        self.assertIn("ipv4", instance_data)
        self.assertIn("ipv6", instance_data)

        # Check some ipv4 entries
        ipv4_entries = instance_data["ipv4"]
        self.assertTrue(len(ipv4_entries) > 0)

        # Check a known destination entry
        dest_406017 = [e for e in ipv4_entries if e.get("destination") == "406017"]
        self.assertTrue(len(dest_406017) > 0)
        entry = dest_406017[0]
        self.assertEqual(entry.get("prefix"), "96.109.183.225/32")
        self.assertEqual(entry.get("algorithm"), "spf")
        self.assertEqual(entry.get("cost"), 2441)
        self.assertEqual(entry.get("tag"), "5")
        self.assertEqual(entry.get("priority"), "High")
        self.assertEqual(entry.get("nh_address"), "96.217.0.229")
        self.assertEqual(entry.get("interface"), "bundle-178")
        self.assertEqual(entry.get("egress_label"), "N/A")
        self.assertEqual(entry.get("nexthop_srgb_base"), 406017)

        # Check some ipv6 entries
        ipv6_entries = instance_data["ipv6"]
        self.assertTrue(len(ipv6_entries) > 0)

        # Check a known ipv6 destination entry
        dest_606017 = [e for e in ipv6_entries if e.get("destination") == "606017"]
        self.assertTrue(len(dest_606017) > 0)
        entry6 = dest_606017[0]
        self.assertEqual(entry6.get("prefix"), "2001:558:4c0:0:3001::22/128")
        self.assertEqual(entry6.get("algorithm"), "spf")
        self.assertEqual(entry6.get("cost"), 2441)
        self.assertEqual(entry6.get("tag"), "5")
        self.assertEqual(entry6.get("priority"), "High")
        self.assertEqual(entry6.get("nh_address"), "fe80::8640:76ff:fe3b:39ed")
        self.assertEqual(entry6.get("interface"), "bundle-178")
        self.assertEqual(entry6.get("egress_label"), "N/A")
        self.assertEqual(entry6.get("nexthop_srgb_base"), 606017)

if __name__ == "__main__":
    unittest.main()