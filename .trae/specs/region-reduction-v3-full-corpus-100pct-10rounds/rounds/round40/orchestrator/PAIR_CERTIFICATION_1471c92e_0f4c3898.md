PAIR CERTIFICATION (orchestrator, 2026-10-13 10:44-10:48, mirror D:/Temp/r91m)

base pair
  analyzer  1471c92eca157e46   rounds/round40/r93/region_analyzer_R21-64a_FINAL.py   (r93a / R21-64)
  generator 0f4c3898298e6f2e   rounds/round40/r95/region_ast_generator_R21-66_0f4c3898298e6f2e.py (r95a / R21-66)

fast gate on the pair (one command, rounds/round40/orchestrator/fastgate_r91m.py --full)
  repro (12-line duplicated while-test) : ***<module>.sync_worker: Different bytecode / units=1/2
  battery (round-14, neighbouring family): RED=8 / 9   ROOT=D:/Temp/r91m   (mirror copy, so it grades the mirror)
  broker                                 : ***TradeLiveBroker._sync_worker: Different control flow / units=127/128
  _sync_worker windows (opcode-name only): windows=5   (landed bytes: 9)
  panel: realtime 12/13  function 15/15  replace_utils 9/9  quote 92/92  quotation 153/153  order_api 37/37

corpus sweep (402 products regenerated from the pair, CR-stripped vs `git archive HEAD site-packages`)
  chunk 1: DONE files=402 same=401 changed=1 newprod=0 nooutput=0 elapsed=206s
  independent re-walk: compared=402 changed=1
    CHANGED site-packages\IQEngine\plugins\plugin_system_trade	rade_live_brokerOK.py  176226->175740
  provenance cross-check: sweep product and fast-gate product are byte-identical CR-stripped (178790 B each)

distance to the flip (rounds/round40/orchestrator/gold_diff_r91m.py vs r91/broker_GOLD_PROOF.py, judged 128/128)
  ours=42 lines  GOLD=45 lines  hunks_vs_GOLD=2
    @@ -18,0 +19,8 @@    GOLD nests the reconnect chain four deep, ending in `return`, between the two loops
    @@ -37,5 +44,0 @@    the same five lines, flat and ending in `break`, after loop 2 in ours
  => ONE statement, cause pinned by r95a's read-only region dump: blocks @1214..@1876 have owner=LoopRegion@232
     (no declared region) while @1890 begins LoopRegion@1890, and _loop_postprocess appends back_edge_stmts after
     body_stmts (region_ast_generator.py:14723/14725/14727).

disposition
  The pair is banked, NOT installed: zero measured unit flips (standing rule - a zero-flip candidate does not consume
  the gate label). It is the certified platform for R21-72 (analyzer declaration) or R21-67 (generator deferral
  conjunct), whichever measures `gold_diff=0 hunks` and `units=128/128` first; installs go through
  orchestrator/install_pair.py, which refuses a non-zero hunk count.
