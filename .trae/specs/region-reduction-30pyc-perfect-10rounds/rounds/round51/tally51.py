# -*- coding: utf-8 -*-
"""Round 51 G1/G2'/G3 tallies recomputed from the stored jsonl (no decompilation)."""
import sys
sys.path.insert(0, 'D:/Temp/r51b')
import gate51 as G

R = 'D:/Temp/r51b/'
G.tally(R + 'g1_head.jsonl', R + 'g1_cand.jsonl', 'G1 (17 deficit<=2 files)')
G.tally(R + 'bat43_head.jsonl', R + 'bat43_cand.jsonl', "G2-prime (143 battery files)")
G.tally(R + 'anch43_head.jsonl', R + 'anch43_cand.jsonl', 'G3 (109 load-bearing anchors)')
