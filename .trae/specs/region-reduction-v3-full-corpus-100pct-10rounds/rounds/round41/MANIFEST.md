# MANIFEST — r103a / FIX_R21-76 (round 40, clock_worker)

Engineer: r103a. Owned: none (no pipeline edit). Platform pair (byte-unchanged, repo==mirror):
  core/cfg/region_analyzer.py       sha256[:16]=1471c92eca157e46
  core/cfg/region_ast_generator.py  sha256[:16]=566ff5c502276e48

RESULT: 13/13 GOLD oracle for <module>.RealtimeEventSource.clock_worker (co_code byte-identical to original).
Pipeline product NOT flipped (12/13): unit is a 6-sub-fact conjunction; no single rule reaches 13/13.

| file | sha256 |
|---|---|
| FIX_R21-76_clock_worker_shared_body_entry_plus_positive_tail_claim.md | 8ec8d94a2a17991fbf43a52295249ca22935b730f4a27a88b74050cdaa6d3d79 |
| GOLD_realtime_event_source_PROOF.py | a8941f27d40c0ca60ee6340013942795a254738420f1c0ca157338feb56d0555 |
| GOLD_varA_holiday.py | b09ea600474317b24df868f33fef03296e33dcfd990e6824709f2e9f55b704be |
| GOLD_varB.py | b29313a1760f3d2acd40dda5d0a1c7df30c9324e888b801f8727f7e1c3f96bf5 |
| GOLD_varC.py | 4f5a11ef8b17de5acce3df27d0ebf47375f883b4a0965775f8ccca5f02700a9a |
| GOLD_varD.py | c435988c815385c966a89fcc95d0c5264e6ade187fe399c3a54696d382fb0d53 |
| GOLD_varE.py | 5226a7463b8aa304720d362eef5d54b9eddd9ce922270b112d6fcd5387fb9286 |
| GOLD_varF.py | a8941f27d40c0ca60ee6340013942795a254738420f1c0ca157338feb56d0555 |
| _step_varA.py | 4296f9e8b61b0db422aa96a6c238ce7f4b2011cee6273cdde658747ab718338b |
| _step_varB.py | 24dcc79d79270244f12ad72cecdd0f8e156ba82baa8ad3bc05ef7512b09f1d40 |
| _step_varF.py | aa6119b56d1baf726e4babe11489bc83facb394b953e817738be1160ffa21dc9 |
| _unchanged_region_analyzer_1471c92eca157e46.py | 1471c92eca157e46d839cdae68c3d3ee325d09a8bb6c3ae8835d3a5450f78bb3 |
| _unchanged_region_ast_generator_566ff5c502276e48.py | 566ff5c502276e48a458669af94131803c0402eed9b3359258fbf9d2cae8ae22 |
| build_gold.py | 8db9f27ac6d147de85b7bbe605ce325d549ccea5fb0925c9ee4222572efb2c76 |
| build_gold_oracle.py | c1c82108c2b33eae1513d6955aa197e49ee76c9011edac86309b4ece5a95e68b |
| build_varC.py | 2a91c526a6ccce27ec939a24d14b91f5317583fa80171188c2c2b39f5db0a083 |
| build_varD.py | ed4d43777d6c6efb241776ed5daa106dd01caaf1667449ce2b90245ab776fea1 |
| build_varE.py | c084233dce6ffae9c5918baf133a722df856efa2cc71a6edc71107370bfc599d |
| cw_full_dis.txt | 4a751221c063af5716c115aeed760babc3eefb7d071b7687d19fff501981103c |
| ladder.txt | c3ef6b9d4aef7dc5554dde9e759dfc8698905d47eaaa91570c9ada4fa251332a |
| panel_base.py | b2e067c72141191109aec4ef04367e12a1a13f4da721ab4d6b7110cd09402c4b |
| rt_base_under_landed_platform.py | 174e1174f28a669cf751b5bc43943d765ddb49f605207daf553796484251716b |

KEY EVIDENCE:
 - GOLD_realtime_event_source_PROOF.py -> pyc_verify single --source -> status=success units=13/13
 - ladder.txt -> rt_base -113/7 -> varF 0/0 13/13 (varE 0/0 still failure: landing-only diff)
 - panel_base.py -> broker 128/128, function 15/15, replace_utils 9/9, quote 92/92, quotation 153/153, order_api 37/37, realtime 12/13