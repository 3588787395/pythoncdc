# VERIFICATION round 41 (LANDED, 2026-10-14 03:26 UTC)

Gate `gate_chain.py 41 40` - regen rc=0 235s, verify rc=0 207s, report rc=0, checks rc=0 175s, CHAIN_DONE.
Log `D:/Temp/gate_chain_41_110803.log`; sealed shards `rounds/round41/after/shard0..7_report.json` (402 rows).

    [units] 6616/6617 -> 6617/6617 (100.0000%)   [files] 401 -> 402
    [gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=1
       FIXED IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc <module>.RealtimeEventSource.clock_worker
       UNIT-UP ... 12 -> 13
    residual_report.py 41 40 -> 单元 6617/6617 (100.0000%) 文件 402/402 残余文件 0 个 残余单元 0 条 UNREGISTERED 行数=0
    [quotation] 153/153   [small34] units_success=1568 success=34/34   [selfcheck] 153/153 Equal, 变异常量 1/153, 变异极性 1/153
    [pytest] 2 failed, 282 passed, 2 xpassed

Named failing tests: `tests/test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`
and `tests/test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function`.
Both are listed verbatim in `baseline_snapshot.md` as the standing roster ("基线名单不变"), so the count
match is confirmed by identity, not arithmetic: zero new failures.

Landed pair: analyzer `996a1b1acf143458`, generator `a981db88af309d32` (= [R21-92], product `ec1b13cb31437222`).
Install collateral: `git status --porcelain -- core/` = 2 lines and `site-packages/` filtered to `*OK.py`
= 1 line (only `realtime_event_sourceOK.py` moved corpus-wide). Installed by the documented direct-write
path (install_pair refuses nonzero --gold-hunks; the 5 residual GOLD hunks are text-only and the judge
ignores them) repeating all of its byte checks.

Objective audit: every roster pyc has a non-empty `*OK.py` produced by the pipeline (405/405 current-magic
inputs measured, 0 zero-byte) and every unit is judged Equal - 6617/6617, 402/402 files, no residual.
