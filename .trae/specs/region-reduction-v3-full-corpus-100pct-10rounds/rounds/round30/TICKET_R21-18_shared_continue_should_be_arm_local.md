# TICKET R21-18 (round 30, pre-digested) — a shared post-chain `continue` must become an arm-local `continue` when the merge block is the loop's back edge

Repo: `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`.
Owner file: `core/cfg/region_ast_generator.py` ONLY (sealed bytes after gate 29 = **`fd0e4c4d73cf5efc`**;
`region_analyzer.py` = `35e227ac3e7b25af`, `ast_generator_v2.py` = `beeaf14435e22922`).
Use mirror `D:/Temp/r33/wt`, products `D:/Temp/r33/out/`. No git writes. Read-only repo.

## 0. Victim and the flip it buys
`IQCommon/api/klinedata.pyc` :: `<module>.get_kline_by_count_new` — the file is **63/64** and this is
its ONLY failing unit ⇒ flip = whole-file **64/64** (393 → 394).
Measured on the sealed product: `len orig=642 prod=642 delta=0 hunks=1 landings=2 judge_diff=True`.
The ledger claim "klinedata needs two sites" is **stale** (superseded by gates 22/25/26/27/28/29).

## 1. The one-hunk defect, measured for you
```
ORIG idx566 @2920 STORE_SUBSCR  (history_data_dict[symbol] = bars_ndarr / bars_ndarr[fields])
ORIG idx567 @2926 JUMP_BACKWARD -> off1268      # the loop's own back edge, emitted INSIDE this arm
PROD idx566 @2918 STORE_SUBSCR
PROD idx567 @2924 JUMP_FORWARD  -> ~off3074/3076 # reaches the SHARED back edge placed after the chain
```
and both sides keep a second back edge at the else-arm tail (`idx603 JUMP_BACKWARD -> off1268`), so
the original has **two** direct back edges where the product has one back edge plus one forward hop.
Emitted text (`klinedataOK.py:298-307`):
```python
                elif fq is not None and fq in DIVIDEND_CALC_TYPE and len(dividends_stock) > 0:
                    symbol_four = symbol.replace('SS', 'XSHG').replace('SZ', 'XSHE')
                    if symbol_four not in dividends_stock:
                        history_data_dict[symbol] = bars_ndarr if fields is None else bars_ndarr[fields]
                    else:
                        ...
                        history_data_dict[symbol] = exrights_bars_ndarr if ... 
                continue            # 307  <- the shared continue that steals the arm-local back edge
```
The two earlier arms (`:294`, `:297`) DO carry their own `continue`, which is why they match.

## 2. The site — already pinned by me with a proven-inert line trace
`region_ast_generator.py:22061-22095` (the R68 route `_r68c3_*`): when the enclosing loop's
`continue_map` labels the `IfRegion.merge_block` as `'CONTINUE'` and that merge block is a *pure*
`JUMP_BACKWARD` into `header_block`, it appends `_r68c3_cont = {'type': 'Continue'}` **after
`if_result`** (line 22090-22093) and marks the merge block generated.
Trace evidence for this file (rig `D:/Temp/t30/tracbreak.py`, product `cmp`-identical to sealed ⇒
inert, positive control 5 332 129 module line events): `'type': 'Break'` sites fire **0** times, and
`'type': 'Continue'` sites fire at `18366×2, 22089×2, 26064×13, 26309×5, 28780×1, 53677×13`.
So the klinedata continue is created at `:22089` — a *statement* emission, i.e. inside the one channel
the generator actually has (AST carries no jump operands; see
`.trae/specs/.../rounds/round20/ADJUDICATION_R20_MERGE_LANDING_FALSIFIED.md`).

## 3. Criterion to implement
When the `IfRegion` whose merge block is the loop's `CONTINUE` block has **more than one arm reaching
that merge** (i.e. `merge_block.predecessors` contains tails of ≥2 arms) and the arm that is NOT the
last in the chain ends there, emit the `Continue` **inside each such arm's body** instead of appending
one after the whole chain; keep the post-chain append for the single-arm case. Rationale: CPython lays
out a `continue` inside an arm as a direct `JUMP_BACKWARD`, and the last arm's tail already falls to
the loop's own back edge — exactly the original's two back edges.
The block data needed is all region-local: `region.merge_block`, `region.then_blocks`,
`region.else_blocks`, `merge_block.predecessors`, `loop.continue_map`, `loop.header_block`,
`loop.back_edge_block(s)` — all already read by the existing route at `:22061-22088`.

## 4. Acceptance (quote the literal rig lines)
`python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py IQCommon/api/klinedata.pyc "<module>.get_kline_by_count_new" --all`
must read `len orig=642 prod=642 delta=0 hunks=0 landings=0 judge_diff=False`, and
`scripts/pyc_verify.py single <abs .pyc> --source <product>` must print `Equal` with the file at 64/64.

## 5. Anti-regression duties (mandatory; this route is SHARED, expect wide fires)
1. Fire census over the 14-file panel used in round 29 (`quotation`, `quote`, `klinedata`, `handlers`,
   `wizard_quant_api`, `trade_info_utils`, `api_base`, `real_quote`, `strategy`, `order_api`,
   `trade_live_broker`, `matcher`, `realtime_event_source`, `risk_calculation/__init__`) reporting
   `TOTAL_FIRES` and, per file, whether its product changes **at all** — compare against
   `git show HEAD:<path>` bytes or the gate's file-level diff, NEVER against the checked-out file
   (checkout is CRLF, the decompiler writes LF, so `cmp` reads DIFF everywhere; that artifact cost this
   campaign a false "four files changed bytes" claim in round 29).
2. `fly/data/quotation.pyc` stays 153/153. Counts that must not drop: `handlers` 29/30,
   `wizard_quant_api` 58/58, `real_quote` 45/45, `trade_info_utils` 38/41, `api_base` 27/28,
   `strategy` 26/27, `order_api` 37/37, `matcher` 17/17, `broker` 121/128, `quote` 91/92,
   `risk_calculation` 42/43, `realtime_event_source` 12/13.
3. All six batteries at their recorded values (repro 9R/9, arm 0G/3R, ccneg 3G/1R,
   retbreak 2G/2R DRIFT=0, orderapi 5G/0R, tail 13G/0R).
4. Probes must be `cmp`-proved inert per target; prefer the line-event trace rig
   (`D:/Temp/t30/tracbreak.py`) over hand-picked line probes — it is what pinned this site in one run.
5. Judge by diff SHAPE (`delta/hunks/landings`), never by the list of failing unit names.

## 6. Deliverable
`D:/Temp/r33/DELIVER/FIX_R21-18.md` (sections 0-7 as in the round-29 tickets) plus
`D:/Temp/r33/DELIVER/CANDIDATE_region_ast_generator.py` (whole file, its `sha256sum | cut -c1-16`)
only if acceptance is met with no panel regression. If the criterion must be narrowed to avoid wide
byte churn, deliver the narrowed version and report the fire census — a measured negative with the
census is accepted and banked.
