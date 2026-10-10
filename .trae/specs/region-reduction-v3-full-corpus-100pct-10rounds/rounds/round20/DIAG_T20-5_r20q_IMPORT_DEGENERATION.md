# FIX_T20-5_DIAG — diagnosis-only report, engineer `r20q`

## STEP-1 header: scope + sealed hashes

Ticket unit: `<module>.PluginRiskCalculation._on_publish_after_trading_end` in
`site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`
Defect: a function-local `import` statement is not emitted.
Reported measurement: `len orig=528 prod=524 delta=-4 hunks=3 landings=1 judge_diff=True`; file reads 41/43.

Repo (READ-ONLY for this run): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
branch `rr-v3r01-f557fd`, HEAD `6f7f9e51c938d2c8fa642acb031c77281d3361b2`

Sealed hashes re-read from CURRENT repo bytes (sha256 first 16 hex) — all three match the ticket:
```
dff6e81a5f2ff9f6  3742423  core/cfg/region_ast_generator.py
beeaf14435e22922  1541302  core/cfg/ast_generator_v2.py
640d33a77dcb71c2  2084706  core/cfg/region_analyzer.py
bbc73f9ebaede624   152912  core/cfg/comprehension_generator.py   (extra, not sealed in ticket)
cf4e2705ab042732    39344  pycdc.py                              (extra)
```

Scope discipline for this run:
- No repo file edited; no git write of any kind.
- Any patching happens only in the mirror `D:/Temp/r20q/wt`, sha256-verified at copy time, restored byte-exactly at the end.
- Products only in `D:/Temp/r20q/out`; no `*OK.py` written into the repo.
- Not running the 402-file gate or full `pyc_verify batch`.
- Other units in this file (`_save_testds_to_csv`) and `D:/Temp/r20n` are out of scope.

Status: IN PROGRESS (sections appended as work proceeds).

---

## 判据/取证 STEP 2 — mirror built, proven reproducing the sealed product

Mirror `D:/Temp/r20q/wt` (copy of `pycdc.py core parsers utils bytecode scripts`, `__pycache__` excluded):
```
repo_files=99 mirror_files=99 only_repo=[] only_mirror=[]
compared=99 mismatch=0
PAIR OK repo=cf4e2705ab042732 mirror=cf4e2705ab042732 pycdc.py
PAIR OK repo=dff6e81a5f2ff9f6 mirror=dff6e81a5f2ff9f6 core/cfg/region_ast_generator.py
PAIR OK repo=beeaf14435e22922 mirror=beeaf14435e22922 core/cfg/ast_generator_v2.py
PAIR OK repo=640d33a77dcb71c2 mirror=640d33a77dcb71c2 core/cfg/region_analyzer.py
PAIR OK repo=097312b88270c461 mirror=097312b88270c461 core/cfg/ast_converter.py
PAIR OK repo=28aba10bae133952 mirror=28aba10bae133952 core/cfg/code_generator.py
PAIR OK repo=bbc73f9ebaede624 mirror=bbc73f9ebaede624 core/cfg/comprehension_generator.py
```
Full 99-line pair table: `D:/Temp/r20q/mirror_hashpairs.txt`. Pristine copy: `D:/Temp/r20q/pristine/wt`.

Pristine-mirror run (6.1 s):
`python -X utf8 pycdc.py <...>/__init__.pyc --region -o D:/Temp/r20q/out/pristine_region.py`
`cmp out/pristine_region.py site-packages/.../__init__OK.py` -> **IDENTICAL** (55589 B).
Every later reading is cmp-ed against this file; any product that differs *and* is meant to
be an inert instrumentation run is void.

Reproduced ticket measurement (repo rig, repo sealed product):
`len orig=528 prod=524 delta=-4 hunks=3 landings=1 judge_diff=True`  (matches the ticket).
NOTE the rig's `--all` is parsed but never passed into `main()` (`unit_diff.py:154-162`), so the
3 hidden hunks are invisible even with `--all`. Re-dumping the raw difflib opcodes myself:

```
== delete orig[480..481] @2748 prod[480..480] del=1 ins=0
   - @2748  LOAD_CONST   0
== delete orig[482..484] @2752..@2754 prod[481..481] del=2 ins=0
   - @2752  IMPORT_NAME  IQEngine.plugins.plugin_system_risk_calculation.function
   - @2754  IMPORT_FROM  THREAD_STATUS
== delete orig[485..486] @2758 prod[482..482] del=1 ins=0
   - @2758  POP_TOP
```
The 4 lost instructions are exactly the `from X import Y` machinery **minus its two survivors**:
`@2750 LOAD_CONST ('THREAD_STATUS',)` (the fromlist) and `@2756 STORE_FAST THREAD_STATUS` are KEPT.
Product text line 253 (inside `while True:`): `THREAD_STATUS = ('THREAD_STATUS',)`.
So the import is not silently skipped — it is emitted **degenerated into an assignment of the
fromlist tuple to the imported name**. (Ticket phrasing "not emitted" = the statement's identity.)
