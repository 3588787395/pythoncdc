# FIX_T20-9 — r20u — T20-9 terminal-exemption override in `_check_elif_chain` (region_analyzer.py only)

Ticket: T20-9. File owned: `core/cfg/region_analyzer.py`. `region_ast_generator.py` / `ast_generator_v2.py`
untouched (mirror holds SEALED bytes, sha16 `4f295dfc6ebd2caa`). Branch `rr-v3r01-f557fd`.
Repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` read-only; all products under `D:/Temp/r20u/out`.

## Mirror build proof

Reused `/d/Temp/r20s/wt` (`cp -r`), then **resynced every code dir from the repo disk** because r20s's
mirror was not pristine:

| file | bytes | sha256[:16] | state |
|---|---|---|---|
| `wt/pycdc.py` | 39344 | `cf4e2705ab042732` | == repo disk |
| `wt/core/cfg/region_analyzer.py` (target) | 2084706 | `640d33a77dcb71c2` | == repo disk == `pristine/region_analyzer.py` |
| `wt/core/cfg/region_ast_generator.py` | 3744157 | `4f295dfc6ebd2caa` | **SEALED restored** — arrived as `7d4c0dfe48b44412` (r20s in-test candidate lineage, brief said "may equal sealed bytes": it did NOT) |
| `wt/core/cfg/ast_generator_v2.py` | 1541302 | `beeaf14435e22922` | == repo disk |
| `wt/scripts/pyc_verify.py` | 18122 | `fe1902a90cebd4a1` | re-copied (see drift below) |

Whole-tree check: 97 `.py` files under `core parsers utils bytecode scripts` + `pycdc.py` compared to repo disk → **mismatch 0**. All `__pycache__` deleted.
Harness: `/d/Temp/r20u/run_panel.sh` (13-file panel, cloned from r20s with paths rewritten), `/d/Temp/r20u/run_batteries.sh` (six batteries), `/d/Temp/r20u/measure1.sh` (single-file regen + judge + unit_diff), `/d/Temp/r20u/probe_sig.py` (read-only region census), `/d/Temp/r20u/patch_r20u.py` (byte-preserving apply/revert).

**Drift #1 (rig, caught by a crash):** at copy time (10:52:45) the repo's `scripts/pyc_verify.py` was
mid-edit and raised `IndentationError` at line 175 → my first Stage-1 panel produced 14 `gen_rc=0
judge_rc=1` rows with **no `units=`/`status=`** (void). The repo file was fixed 25 s later (10:53:10,
commit `65a331ea` "ruler: single-mode now prints a provenance NOTE"); I re-copied it and re-ran Stage 1.
**Drift #2 (`git show HEAD:` ≠ disk):** HEAD bytes differ for every patched file (HEAD `region_analyzer.py`
= 2052055/`9f6022ec5a6b1c72`) — Windows CRLF checkout conversion. Disk == sealed (matches r20s's sealed
sha16 for `region_ast_generator.py`), so all anchors are against disk bytes.
**Drift #3 (self-cert target):** the repo **root-level** `quotationOK.py` (183755/`7358496efa643229`) is a
stale copy; the gate product is `site-packages/fly/data/quotationOK.py`. Self-certification against the
latch: my unpatched mirror regenerates `site-packages/fly/data/quotationOK.py` at
**182759 / `302f449afc9245eb` — byte-IDENTICAL (raw `cmp`, no normalization)** to the repo's committed
product. Mirror certified.

## Stage 1 baseline (UNPATCHED mirror) — PASS, all 14 files + 6 batteries at recorded values

`out/stage1/panel_summary.txt`:
fly/data/quote **87/92** · klinedata **63/64** · handlers **29/30** · wizard_quant_api **55/58** ·
trade_info_utils **38/41** · api_base **27/28** · real_quote **43/45** · strategy **26/27** ·
realtime_event_source **12/13** · risk `__init__` **42/43** · trade_live_broker **118/128** ·
SENT quotation **153/153 success** · SENT matcher **17/17 success** · SENT order_api **37/37 success**.
Batteries `out/stage1/battery_summary.txt`: repro **RED=9/9** · arm **GREEN=0 RED=3** · ccneg **GREEN=3 RED=1** ·
retbreak **GREEN=2 RED=2 DRIFT_VS_BASELINE=0** · orderapi **GREEN=5 RED=0** · tail **GREEN=13 RED=0** — all recorded.

## Signature re-verification (BEFORE any predicate)

`python -X utf8 probe_sig.py site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc "<module>.RealQuoteData.get_tick_direction"`
(read-only driver in its own process; no analyzer patch; `out/sig_real_quote.txt`):

```
regions_total=31 IfRegion_count=10 merge_None_count=1
IfRegion[NOMERGE] entry=1112 cond=1112 merge=None
   then=[1124, 1126]
   else=[1128, 1174, 1176, 1388, 1224, 1332, 1390]
   elif_conditions=0 elif_bodies=0 elif_final_else=[]
     [else b=1332] tail=JUMP_BACKWARD argval=1174 succ=[1460, 1174]     <- the ticket's "back tail"
     [then  b=1126] tail=RETURN_VALUE ; [else b=1390] tail=RETURN_VALUE  <- BOTH arms terminal
```
CONFIRMED exactly: one IfRegion, one merge-less IfRegion, entry/cond/then/else lists and the `else 1332 JUMP_BACKWARD` tail as quoted.

**REFUTED by the same measurement (the ticket's causal premise):** block 1332's `JUMP_BACKWARD` is a
**for-loop back edge to 1174, both inside the region's own else arm** (`IfRegion entry=1176 ... merge=1332`
and `FOR_ITER @1174 -> 1388` prove it); it is not an arm that "terminates in a backward jump out of the
region". Region 1112 has **no merge to declare** — both arms end in `RETURN_VALUE` (@1126, @1390) — and it
contributes **zero** diff: in the sealed product orig idx 201..288 vs prod idx 202..289 match
instruction-for-instruction (only a +2-byte shift shadow). The ticket's `delta=0 hunks=0 landings=2`
**does not reproduce on sealed bytes**: sealed reads `delta=1 hunks=1 landings=1` (measured twice:
fresh mirror product AND the repo's committed in-place `real_quoteOK.py` — identical readings). That
`0/0/2` shape was measured with r20s's non-landed `region_ast_generator.py` candidate installed (it deletes
the dead `JUMP_FORWARD` but keeps the wrong shape).

**Where the two misplaced targets actually are** (sealed bytecode, from `dis` of the pyc):
```
@858  LOAD_FAST redata / POP_JUMP_IF_FALSE 944            if redata:
@942  JUMP_FORWARD  -> 1106                                (then-arm tail; 1106 = merge_ = next stmt `try:`)
@944  LOAD_FAST flag == 1 / POP_JUMP_IF_FALSE 1024         (nested chain, else 臂首块)
@1022 JUMP_FORWARD  -> 1102                                flag==1 臂末汇于 1102，不是 1106
@1024 LOAD_FAST flag == -1 / POP_JUMP_IF_FALSE -> 1102     flag==-1 测试假边汇于 1102
@1100 POP_TOP  (fallthrough)                               -> 1102
@1102 LOAD_FAST redata / @1104 RETURN_VALUE                1102 = 尾随语句 `return redata`
```
True source shape: `if redata: redata=… else: (if flag==1: … elif flag==-1: …); return redata`.
Sealed analyzer instead flattens it: `IfRegion entry=858 merge=1106 elif_conditions=2 elif_bodies=2
elif_final_else=[1102]` — a **phantom else**, and that is what emits the dead `JUMP_FORWARD @1102` and
mislands @1022/@1034. (Nested `IfRegion entry=944 merge=1102` already exists as its own abstract node.)

## 判据实现

`D:/Temp/r20u/wt/core/cfg/region_analyzer.py:22360-22367` (inserted after pristine `:22346`, inside
`_build_elif_region` → nested `_check_elif_chain(header_, else_blocks_, merge_)`, immediately below the
existing 判据①②③⑤ `_d2_terminal` guard at `:22337-22346` and above the `[R48-C]` predicate):

```python
                if (_d2_terminal and inner_merge.start_offset < merge_.start_offset):
                    for _t9_tb in then_blocks:
                        _t9_last = _t9_tb.get_last_instruction()
                        if (_t9_last is not None
                                and _t9_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                and _t9_last.argval is not None
                                and _t9_last.argval == merge_.start_offset):
                            return None
```
Predicate in words: the ⑤ terminal-exemption is overridden — i.e. the region **declares at identification
time that it is not an elif chain** — when `inner_merge` (the else-arm-head's own convergence block) is
terminal **and** the region's own `then` arm lands on the outer merge `merge_` at a strictly later offset,
so `inner_merge` lies *inside* the else arm and its terminal block is the else arm's trailing statement
(the nested chain's merge is declared by the nested region itself, `entry=944 merge=1102`). Returning
`None` is the existing, one-way declaration channel: the caller then builds IF_THEN_ELSE from the region's
own `else_blocks`, the nested if stays a child IfRegion (原则 3), and the terminal block stays a sibling of
the else arm (原则 2, unique membership). No sibling-region read, no retrospective repair, no ordering
dependence (`then_blocks`, `inner_merge`, `merge_` are all this region's own data at this point), no
name/constant/offset special-casing.

## stage readings (patched mirror, `out/cand/`)

Target unit, `unit_diff.py` sealed-vs-candidate product, `get_tick_direction`:
`len orig=295 prod=295 delta=0 hunks=0 landings=0 judge_diff=False` (sealed: `delta=1 hunks=1 landings=1 judge_diff=True`).

Panel, judge with `--source <fresh product>` (14/14 files; **zero decreases**):

| file | stage1 | candidate |
|---|---|---|
| fly/data/quote.pyc | 87/92 | **88/92** (+1, `<module>.Quote.get_individual_data` now Equal: `1/1/1 True` → `0/0/0 False`) |
| IQData/plugins/…/real_quote.pyc | 43/45 | **44/45** (+1, **named unit `get_tick_direction` flipped**) |
| IQCommon/api/klinedata.pyc | 63/64 | 63/64 (unchanged) |
| IQCommon/logger/handlers.pyc | 29/30 | 29/30 |
| IQCommon/strategy/wizard_quant_api.pyc | 55/58 | 55/58 |
| IQCommon/util/trade_info_utils.pyc | 38/41 | 38/41 |
| IQData/api/api_base.pyc | 27/28 | 27/28 |
| IQEngine/…/strategy.pyc | 26/27 | 26/27 |
| IQEngine/…/realtime_event_source.pyc | 12/13 | 12/13 |
| IQEngine/…/risk_calculation/`__init__`.pyc | 42/43 | 42/43 |
| IQEngine/…/trade_live_broker.pyc | 118/128 | 118/128 |
| SENT fly/data/quotation.pyc | **153/153 success** | **153/153 success** |
| SENT …/matcher.pyc | **17/17 success** | **17/17 success** |
| SENT …/order_api.pyc | **37/37 success** | **37/37 success** |

Batteries with the patch (all at recorded values): repro **RED=9/9** · arm **GREEN=0 RED=3/3** ·
ccneg **GREEN=3 RED=1/4** · retbreak **GREEN=2 RED=2, DRIFT_VS_BASELINE=0** · orderapi **GREEN=5 RED=0/5** ·
tail **GREEN=13 RED=0/13**.

Blast radius / inertness proof (no in-analyzer probe was ever installed — `probe_sig.py` is an external
read-only driver, and every reading above comes from a regenerated product): candidate products compared
to Stage-1 products, CRLF-normalized → **exactly 2 of 14 changed** (`IQData__plugins__real_quote_OK.py`,
`fly__data__quote_OK.py`), the other **12 byte-identical**. No file decreased. Judge's failing-unit list for
both changed files diffed: 1 unit removed from each, **0 newly failing** (`out/{s1,cand}_quote_fail.txt`,
`out/{s1,cand}fail.txt`).

## 负面证据

1. **The ticket's named region is not the defect site.** `IfRegion entry=1112 merge=None` keeps
   `merge_block=None` under my patch (unchanged in `out/sig_real_quote_cand.txt`) and the unit still flips
   to clean, so a merge declaration for 1112 was neither necessary nor possible: its `then` arm terminates
   `RETURN_VALUE @1126` and its `else` arm terminates `RETURN_VALUE @1390` — no fallthrough point exists to
   declare. The quoted "back tail ('else', 1332, 'JUMP_BACKWARD')" is a **for-loop back edge to 1174**, i.e.
   an edge whose source and target are both members of the same arm; it does not leave the region.
   ⇒ "declare a merge at identification time **for the region named in the brief**" = FALSIFIED as stated;
   the same-file, same-shape fix had to be made at the region that actually owns the mislanded arms
   (`entry=858`, arms @956/@1024/@1036 landing on @1102).
2. **`delta=0 hunks=0 landings=2` is not the sealed baseline.** Sealed bytes read `delta=1 hunks=1
   landings=1` both from my fresh mirror product and from the repo's committed in-place `real_quoteOK.py`.
   The quoted shape required r20s's non-landed `region_ast_generator.py` candidate.
3. **Secondary target NOT claimed.** `klinedata :: get_kline_by_count_new` product is **byte-identical** to
   pristine (63/64 unchanged); the criterion never fires there — its merge-less region
   (`regions_total=49 IfRegion_count=21 merge_None_count=1`, `out/sig_kline_cand.txt`) carries loop back
   tails to 1268, and the file is known to need two sites. One patch ⇒ no claim.
4. **wizard_quant_api's 10 merge-less IfRegions untouched** (product byte-identical, 55/58) — as instructed,
   absent-merge there was not modified. Same for `tick_worker_thread` / `clock_worker` /
   `run_individual_transform` (their files' products did not change at all).
5. **No ordering-wall crossing:** the predicate consumes only the region's own `then_blocks`, its own
   `inner_merge` and its own `merge_`; it does not read any sibling region's member list, so parents-before-
   children identification order is irrelevant here (contrast `NOTE_T20_ORDERING_WALL.md`).
6. Cost note: two of the four `JUMP_FORWARD`-style landings in the sealed product (@942) were alignment
   shadows, not real — the unit's only true content defect was the one phantom-else chain.

## final declaration

**LANDED-READY** (one named unit flip + one bonus flip, zero decreases, all sentinels and all six
batteries at recorded values).

- Delivered file: `D:/Temp/r20u/DELIVER/region_analyzer.py` — the WHOLE changed file, 2086658 bytes,
  **sha256 first-16 = `ec6bd48826c65df9`**, `cmp`-identical to `D:/Temp/r20u/wt/core/cfg/region_analyzer.py`
  (mirror state used for every reading above).
- vs pristine (`640d33a77dcb71c2`, 2084706 bytes, 32651 lines): **diff = 1 hunk, +21 added lines, 0 removed**
  (candidate lines 22347-22367; 32672 lines total).
- `py_compile` proof: `python -X utf8 -m py_compile DELIVER/region_analyzer.py` → `PYCOMPILE_DELIVER_OK`
  (also run on the mirror copy before measurement: `PYCOMPILE_OK`).
- Install (whole file, per campaign rule — mirror patches do not `git apply` here):
  `cp /d/Temp/r20u/DELIVER/region_analyzer.py /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_analyzer.py`
- Exact revert command:
  `cp /d/Temp/r20u/pristine/region_analyzer.py /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_analyzer.py`
  (equivalently `python -X utf8 /d/Temp/r20u/patch_r20u.py revert` restores the mirror; pristine sha16
  `640d33a77dcb71c2` verified by `cmp`). No `git` write was made; repo untouched (read-only role).

