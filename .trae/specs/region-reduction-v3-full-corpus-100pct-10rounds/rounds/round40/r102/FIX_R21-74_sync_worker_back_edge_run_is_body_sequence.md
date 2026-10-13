# FIX_R21-74 — `_sync_worker` back-edge run is body sequence (position + terminator)

Engineer: **r102a** · round 40 · unit: `<module>.TradeLiveBroker._sync_worker`
File under test: `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` (127/128)
Owned file: `core/cfg/region_ast_generator.py` ONLY. `region_analyzer.py` is r100a's; untouched.

## 0. Platform (certified pair, installed into mirror `D:/Temp/r102`)

sha16 measured with `hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]`:

| file | sha16 | bytes | BOM | `rrn` | bare LF |
|---|---|---|---|---|---|
| `core/cfg/region_analyzer.py` ← `r93/region_analyzer_R21-64a_FINAL.py` | `1471c92eca157e46` | 2121884 | yes | 0 | 0 |
| `core/cfg/region_ast_generator.py` ← `r95/region_ast_generator_R21-66_0f4c3898298e6f2e.py` | `0f4c3898298e6f2e` | 3860104 | yes | 0 | 0 |

Both match the brief exactly. Repo HEAD pair for reference: analyzer `842e2748bcdfeb66`,
generator `b4363f5858e58074` (gate-39 landed) — i.e. the certified pair is NOT repo HEAD, as expected.

## 1. Base reproduction (BEFORE any edit) — all numbers match the brief

Rig: `$SP/rounds/round40/orchestrator/fastgate_r91m.py` + `gold_diff_r91m.py` + `win_r91.py`
copied to `D:/Temp/r102/orch/` (and `win_r91.py` also at mirror root), `M` repointed to `D:/Temp/r102`.
Round-14 battery copied to the same relative depth (`$M/.trae/specs/…/rounds/round14/repro/`), 59K.

```
[installed] gen=0f4c3898298e6f2e ana=1471c92eca157e46
[repro mechanism A] ***<module>.sync_worker: Failure: Different bytecode / [single] status=failure units=1/2 success_rate=50.00%
[battery no-regression] RED=8 / 9  ROOT=D:\Temp\r102
[broker] ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow / [single] status=failure units=127/128 success_rate=99.22%
[_sync_worker windows] windows=5
[panel realtime] [single] status=failure units=12/13 success_rate=92.31%
[panel function] [single] status=success units=15/15 success_rate=100.00%
[panel replace_utils] [single] status=success units=9/9 success_rate=100.00%
[panel quote] [single] status=success units=92/92 success_rate=100.00%
[panel quotation] [single] status=success units=153/153 success_rate=100.00%
[panel order_api] [single] status=success units=37/37 success_rate=100.00%
```

Log: `D:/Temp/r102/orch/logs_base_full.txt` (transcribed verbatim from that file).

Checklist against the brief:
- judge on broker: `status=failure units=127/128`, sole failure
  `***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow` — **MATCH**
- product size `178790` bytes (CR-stripped `175740`) — **MATCH**
- `_sync_worker` instruction windows `5` — **MATCH**
- battery `RED=8/9` known-good baseline — **MATCH**
- panel: function 15/15, replace_utils 9/9, quote 92/92, quotation 153/153, order_api 37/37
  all green; realtime 12/13 known residual — **MATCH**

**Base reproduced. Editing may begin.**

## 2. The two textual facts that define the flip (confirmed in the base product)

`gold_diff_r91m.py out/base_broker.py` → `unit=_sync_worker ours=42 lines GOLD=45 lines hunks_vs_GOLD=2`,
hunks `@@ -17,4 +17,12 @@` and `@@ -35,8 +43,3 @@`. Reading them:

1. **POSITION.** Our product emits the reconnect chain *after* loop 2
   (`while pre_before_trading <= … < int(post_after_trading):`); GOLD emits it *between*
   loop 1 (`while int(...strftime('%H%M')) < pre_before_trading or …`) and loop 2.
2. **TERMINATOR.** Ours: `if not reconnect(self.broker.trade_account, self.trade_id): break`.
   GOLD: `… : return`.

Flat-vs-nested is the *only* difference the two hunks show beyond 1+2, and it is invisible to the
judge (per the brief's measured probe `r100/PROBE_source_flat_chain_in_place.py`: GOLD with ONLY the
nested 8-line chain swapped for our flat 5-line form, same position, keeping `return`, judges
`[single] status=success units=128/128 success_rate=100.00%`). So the criterion is position + terminator,
and the acceptance test is the judge, not the gold diff.

`win_r91` base windows confirm the same story in instruction space: hunk #4 deletes 87 instructions
at orig `@1210..@1880` and hunk #5 inserts 85 at prod `@2202..@2886` — the run is emitted in the
wrong slot, and the small `del=1 ins=0` / `del=2 ins=0` hunks #2/#3 are the break-vs-return residue.

## 3. Mechanism (already localized by the campaign; not re-diagnosed)

The chain is the block run `@1214..@1876` of the enclosing `while True:` region `LoopRegion@232`.
Those blocks are body blocks with no region of their own (`block_to_region[b] is LoopRegion@232`),
and `@1890` — entry of the child `LoopRegion` that IS loop 2 — is the run's forward target (merge).
They are routed through the loop-exit deferral path instead of being emitted as sequential body
statements at their own offset slot:
- `_loop_process_natural_back_edge` (~`region_ast_generator.py:13844`, called at `:9365`) collects
  them into `back_edge_stmts`;
- `_loop_postprocess` (`:14704`) appends `back_edge_stmts` to `body_stmts` at `:14723/14727/14733`
  (or into an if-body at `:14718`) — i.e. AFTER the child loop already emitted during the main walk.

Appending after the body is what moves the text past loop 2; being in the back-edge/loop-exit list
is what renders that run's terminal block (`@1874`, the function's only `RETURN_VALUE`) as a `break`.

## 4. Plan
1. Fire census BEFORE any edit (panel 20 files, then 402 sharded 8 ways) + inertness cert.
2. Patch: reclassify a forward-exit run whose terminal block is a RETURN-class sink and whose blocks
   all precede a declared child-region entry in the same owner's body as **sequential body code at
   its own offset slot**, inserted into `body_stmts` before that child region.
3. Halves table, panel, 402-file collateral sweep (CR-stripped vs `git archive HEAD site-packages`).
4. Definition of done: `pyc_verify.py single <broker pyc> --source <fresh product>` → `128/128`.

## 5. Correction of the localized mechanism (measured, before editing)

The brief routed the run through `_loop_process_natural_back_edge` / `back_edge_stmts`
(`region_ast_generator.py:13844`/`:14704`). Read-only monkeypatch probes (no file edits; the
analyzer file was never touched — re-hashed `1471c92eca157e46` afterwards) show the actuation
point is one step earlier, and `back_edge_stmts` is empty at that site:

* `dump_r95.py` (analyzer 1471c92e): the chain blocks `@1214,1370,1388,1502,1524,1638,1770,1872,1876`
  are owned by the **outer** `LoopRegion@232(hdr=232)` only — `block_to_region[b] is LoopRegion@232`,
  and they are in **neither** `LoopRegion@1890.blocks` (loop 2) nor `LoopRegion@232(hdr=704).blocks`
  (loop 1). Block `@1872` = `LOAD_CONST None; RETURN_VALUE`, **zero successors**, role `BREAK`;
  every other run block has role `LOOP_BODY`; all run exits go **forward** to `@1890`
  (`@1876 -> @1890`, `@1214 -> {1370, 1890}`, …).
* `_loop_postprocess` trace (`logs_pp_probe.txt`): outer `hdr=232` arrives with
  `body_stmts types = ['While','While','If']`, `pending=[2882]`, `back_edge_stmts=0` — so the chain
  `If` is already in the body list *before* postprocess, and `back_edge_stmts` is empty: this site is
  not the deferral path.
* `_loop_dispatch_block` per-block trace (`logs_diag5.txt`) — the decisive line:

```
[DISP] block@230    handled=False pend_before=[]  added=[]        total=0
[DISP] block@700    handled=False pend_before=[]  added=[]        total=2   <-- total 2: BOTH While nodes
[DISP] block@1214   handled=True  pend_before=[]  added=['If']    total=3
[DISP] block@2882   handled=False pend_before=[]  added=[]        total=3
```

  i.e. loop 2's `While` was emitted **early**, at `block@232`, as loop 1's *sequential-after-loop*
  tail (`_r58_collect_break_target_stmts` for loop 1 resolves break-target `@2064` to
  `bb_region = LoopRegion@1890` and emits it, `logs_r58.txt`/`logs_trigger.txt` frames
  `8677 _r58_collect_break_target_stmts` → `6913 _generate_region(bb_region)`).
  Later, the run `@1214` is dispatched, handled, and **appended at the end** — hence after loop 2.
* So the defect is *append-after-an-early-child-node*, not *loop-exit deferral*: the position and the
  `Break` both come from the run being treated as trailing body code, with `@1872`'s analyzer role
  `BREAK` printed as `break` although the block is a zero-successor `RETURN_VALUE` sink.
* The `Break` is not reachable by the existing fold: `_break_to_return_map_w`
  (`region_ast_generator.py:8599`) is built only from break blocks that *have a RETURN-role successor*;
  `@1872` has none (it *is* the return), so the map stays empty and no fold fires.

## 6. Fire census BEFORE any edit (`census_r102.py`, analyzer-only, generator never runs)

Predicate (block data only): direct child `LoopRegion C` with `entry E ∈ R.body_blocks`, `E > min(run)`;
forward closure `S` from the run whose every exit lands in `S`, exactly on `E`, or in another declared
region's blocks; **exactly one** zero-successor `RETURN_VALUE`/`RETURN_CONST` sink in `S`; no other
`BREAK`-roled block in `S`; no backward exit edge (a genuine back edge jumps backward).

* 20-file panel (`PANEL_20files.txt`, prefixed with `site-packages/`):
  `TOTAL files=20 evals=957 fires=1 files_with_fire=1` — the single fire is the broker, in
  `_sync_worker`: `loop_entry=232 loop_hdr=232 child_entry=1890 sink=1872
  run=[702,1210,1212,1214,1370,1388,1502,1524,1638,1770,1872,1876]`
  (`orch/logs_census_panel20.txt`).
* Full corpus (`corpus402.txt`, 8 parallel shards, `census_shards/`):

```
AGGREGATE files=402 evals=6617 fires=1 elapsed=25s
FILES_WITH_FIRE_SITES=1 ['site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc']
FIRELINE ... _sync_worker ... child_entry=1890 run=[702,1210,...,1876] sink=1872
```

  6617 code objects evaluated, **1 fire, 1 file** — a general rule that happens to fire once.
* Inertness: the census process never imports/calls the generator. Independently, the first candidate
  (which wired the same predicate into the three *flush* sites) regenerated
  `out/fastgate_broker.py` **byte-identical** to the base product
  (`diff lines=0 identical=True`, `logs_patch_full.txt` unchanged 127/128 + panel green), which proves
  those hooks were actuated-but-inert at every site (they never found a qualifying run), so no probe
  perturbation of the CFG.

## 7. Halves table (analyzer `1471c92e` fixed in both rows)

| generator half | sha16 | broker judge | windows | delta | gold hunk | panel |
|---|---|---|---|---|---|---|
| `R21-66` landed | `0f4c3898298e6f2e` | `status=failure units=127/128`, `_sync_worker: Different control flow` | 5 | `-4` (412→408) | 2 | 5 green + realtime 12/13 |
| `R21-74` v1 (flush sites only) | `91c16e1636dddd14` | `status=failure units=127/128` (product byte-identical) | 5 | `-4` | 2 | unchanged |
| `R21-74` v2 (dispatch re-seat added) | `566ff5c502276e48` | **`status=success units=128/128 success_rate=100.00%`** | 4 | `-4` | 1 (flat-vs-nested only; judge-invisible) | unchanged |

`win_r91` patched: `orig instrs=412 prod instrs=408 delta=-4`, `windows=4`; hunk #4/#5 of the base
(`del 87 @1210..@1880` + `ins 85 @2202..@2886`, the run deleted from its slot and re-inserted after
loop 2) are **gone**; what remains is the small `del=1`/`del=2` instruction-count residue at
`@696/@700` and `@1210` that exists in GOLD-parity text too. Patched product size `178823`
(base `178790`).

## 8. Panel after the patch (`orch/logs_patch2_full.txt`)

```
[installed] gen=566ff5c502276e48 ana=1471c92eca157e46
[repro mechanism A] ***<module>.sync_worker: Failure: Different bytecode / [single] status=failure units=1/2 success_rate=50.00%
[battery no-regression] RED=8 / 9  ROOT=D:\Temp\r102
[broker] [single] status=success units=128/128 success_rate=100.00%
[_sync_worker windows] windows=4
[panel realtime] [single] status=failure units=12/13 success_rate=92.31%
[panel function] [single] status=success units=15/15 success_rate=100.00%
[panel replace_utils] [single] status=success units=9/9 success_rate=100.00%
[panel quote] [single] status=success units=92/92 success_rate=100.00%
[panel quotation] [single] status=success units=153/153 success_rate=100.00%
[panel order_api] [single] status=success units=37/37 success_rate=100.00%
```

All six base rows keep their verdict (`realtime` stays 12/13 known residual); the round-14 battery stays
at the known-good `RED=8/9`; the `r90` rotated-while repro stays 1/2 (that is the r93/r91 mechanism-A
axis, untouched by this patch).

## 9. Collateral sweep — 402 products, patched pair, CR-stripped vs HEAD

HEAD products taken with `git archive HEAD site-packages | tar -x` into `D:/Temp/r102/head_sp`
(407 `*OK.py` extracted; never `cmp` against the CRLF-normalized checkout; the repo was not modified).
Regeneration ran from the mirror with `gen=566ff5c502276e48`, `ana=1471c92eca157e46` (post-sweep
re-hash of both mirror core files: analyzer still `1471c92eca157e46` — r100a's file untouched).
8 parallel shards (`sweep_shards/`, driver `orch/logs_sweep_driver.txt`):

```
DONE files=51 same=51 changed=0 ...   (x6 shards)
DONE files=50 same=49 changed=1 ...
DONE files=50 same=50 changed=0 ...
CHANGED site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc (176226 -> 175772 bytes)
```

**`same=401 changed=1`, `newprod=0`, `nooutput=0`, `TIMEOUT=0`; `changed = {trade_live_broker}`** —
exactly the expectation, no collateral. The one changed file is judged in §10.

## 10. Definition of done (fresh product, `--source`)

```
$ python -X utf8 pycdc.py <broker pyc> -o out/dod_broker.py        # mirror pair 566ff5c5 + 1471c92e
$ python -X utf8 scripts/pyc_verify.py single <broker pyc> --source out/dod_broker.py
[single] .../trade_live_broker.pyc
[single] 产物 D:/Temp/r102/out/dod_broker.py
[single] status=success units=128/128 success_rate=100.00%
```

**`status=success units=128/128` reached.**

## 11. What the patch does (`region_ast_generator.py` only, 7 anchored edits)

1. `__init__`: `self._r102_child_node_origin: Dict[int, int] = {}` — an internal ledger from AST node
   identity to the entry offset of the child region that produced it (no AST field added, no text touched).
2. `_r58_collect_break_target_stmts`: when a break target resolves to a structured child region
   (`IfRegion`/`LoopRegion`/`TryExceptRegion`) whose AST is extended into the sequential tail, record
   `entry.start_offset` for the nodes it just produced. This is the region-data fact that says
   "this node is child region E, emitted earlier than the walk's current position".
3. New helpers: `_r102_run_before_child` (the §6 predicate), `_r102_slot_of_child`,
   `_r102_fold_run_break_to_return`, `_r102_reseat_run_return_value`, `_r102_place_body_run`,
   `_r102_reseat_body_run`. All wrapped in `try/except -> fall back to the existing behaviour` (C3).
4. Dispatch site in `_loop_generate_body` (**the actuator**): record `len(body_stmts)` before
   `_loop_dispatch_block`; when dispatch handled the block and appended statements, test the predicate
   on `seeds=[block]`. If the appended run (a) exits forward only into itself or a declared child
   region entry `E`, (b) contains exactly one zero-successor `RETURN_VALUE`/`RETURN_CONST` sink and no
   other BREAK-roled block, and (c) a node with recorded origin `>= E` already sits earlier in
   `body_stmts` — then **move** those freshly created nodes to that slot (insert before the child node)
   and reduce the sink's `Break` arm to the sink's `Return` AST. Nothing else in the body list is
   reordered; the run's blocks stay uniquely owned by the dispatch that already consumed them
   (principles 2 and 4 hold: the child region node is not split, no block is claimed twice).
5+6+7. The same rule is wired into the three *flush* sites (R58-A pre-child flush, pre-dispatch flush,
   `_loop_postprocess` branch flush): they insert instead of appending when the predicate holds. Measured
   inert on this corpus (candidate v1 with these sites only => byte-identical product), kept because the
   rule is general and they are the same defect shape at a different actuator.

No function/file names, no absolute offsets, no counters, no thresholds, no corpus identity tests are
used as matching keys: the criteria are successor-structure (forward-only into a declared child entry),
opcode class (`RETURN_VALUE`/`RETURN_CONST`), zero-successor sink shape, and `BlockRole` of the run's
blocks.

Both textual facts moved:
* **Position** — the chain now prints between loop 1 and loop 2 (gold-diff hunk `@@ -35,8 +43,3 @@` gone).
* **Terminator** — `if not reconnect(self.broker.trade_account, self.trade_id):` now followed by
  `return None` (from `@1872` = `LOAD_CONST None; RETURN_VALUE`), not `break`. The remaining gold diff is
  1 hunk = flat `if A and B and (C or D) and E:` vs GOLD's four nested `if`s, which the brief measured as
  judge-invisible.

## 12. Deliverables (banked in `D:/Temp/r102/DELIVER/`)

* `FIX_R21-74_sync_worker_back_edge_run_is_body_sequence.md` — this doc.
* `region_ast_generator_R21-74_566ff5c502276e48.py` — **final patched generator** (sha16 `566ff5c502276e48`,
  BOM + all-CRLF, `rrn=0`, bare-LF `0`, `py_compile` clean).
* `gen_R21-74_v1_91c16e1636dddd14.py` — the intermediate flush-sites-only candidate (measured inert).
* `build_r102b.py` (final builder), `build_r102b_v1_flush_sites_only.py` (v1 builder).
* `census_r102.py`, `run_census_all.py` (fire census + 8-shard driver),
  `sweep_r102.py` (402-file collateral sweep, repointed to `D:/Temp/r102`).
* Logs: `logs_base_full.txt`, `logs_patch_full.txt` (v1), `logs_patch2_full.txt` (v2 = flip),
  `logs_census_panel20.txt`, `logs_census402_driver.txt`, `logs_sweep_driver.txt`, plus the read-only
  mechanism probes `logs_pp_probe.txt`, `logs_diag5.txt`, `logs_r58.txt`, `logs_render_cmp.txt`.

## 13. Reproduce

```
cd D:/Temp/r102
python -X utf8 build_r102b.py base_gen_0f4c3898.py gen_R21-74_candidate.py
python -X utf8 orch/fastgate_r91m.py --gen gen_R21-74_candidate.py --full     # 128/128 + panel green
python -X utf8 census_r102.py 280 panel20_pref.txt                             # fires=1
bash run_sweep_all.sh                                                          # same=401 changed=1
```
(the sweep regenerates into `sp_out/`; it reads the mirror's installed pair, so run it after installing
`gen_R21-74_candidate.py` into `core/cfg/region_ast_generator.py`, which `fastgate --gen` does.)

