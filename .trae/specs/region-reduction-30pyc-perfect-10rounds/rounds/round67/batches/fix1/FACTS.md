# Round 67 · fix1 · FACTS (narrow J1 → J2, four hard gates)

Workspace `D:/Temp/opencode/r67gate/fix1`. Repo `F:/Downloads/pythoncdc-main` is **read-only**
for this task: no writes to `core/`, `*OK.py`, `pyc_index.json`, `.trae/`, `test_repros/`.
Siblings `diag2..diag6` untouched. No 402-file sweep run here.

Discipline: every command `python -X utf8`, **PYTHONIOENCODING never set**, each command
self-sharded to finish <300 s.

Task: diag1's `cand_r67_j1` (specs/cand_r67_j1.json, copied into this dir) kills the right
defect class on the repro (6/7→7/7, battery untouched) but is **too wide** — it ERRs the named
target and moves the `quotation.pyc` canary sha. Narrow it to the captured frame shape and pass
four gates.

## STEP A — workspace + anchor preflight

Provisioning defect found and fixed **inside this workspace only**: the copied
`h62.py`/`cstrict.py` still had `ROOT/GATE = D:/Temp/opencode/r67gate/diag1`, i.e. my runs would
have written mirrors/builds/products into diag1's directory. Retargeted to
`D:/Temp/opencode/r67gate/fix1` (2 literals). `battery.txt` here is the rebuilt **31-line** list
(diff vs diag1/battery.txt = IDENTICAL; centre copy is the stale 24-line one).

Anchor uniqueness on CURRENT landed bytes (file is **CRLF**, BOM-less; `h62.py build` normalizes
before matching, so a raw byte grep for LF text reads 0 — verified both ways):

```
git status --short core/   -> empty (landed bytes == R66 landing)
normalized landed bytes, J1 anchor occurrences = 1
```

`h62.py build --spec=... --dst=<arm>` additionally asserts `head mirror == worktree bytes`.

## STEP B — the four landed baselines, re-run by me in this dir (all reproduce the brief)

| list | command | reading |
|---|---|---|
| `synth_r67.txt` | `run --arm=landed --out=dump/landed_synth.jsonl` | **6/7**, defect `['v3', 43, 42, 2, 23]` |
| `targets.txt` | `run --arm=landed --out=dump/landed_targets.jsonl` | **107/119**, 12 OFF rows verbatim incl. `get_all_orders 79/78 j2 t24` |
| `battery.txt` (31) | 2 shards → `dump/landed_battery.jsonl` | **115/127, 12 defect functions**, 24 files fully matched |
| `canary.txt` (4) | `run --arm=landed --out=dump/landed_canary.jsonl` | 143/143 `4d41187e356544e0` · 10/10 `af77224b34b203c4` · 26/26 `e711b8ea86d49a15` · 25/25 `9d09af09249da177` |

## STEP C — diag1's banked narrowing is FALSIFIED by measurement (arm `j2`)

`specs/cand_r67_j2.json` (= J1's three conjuncts **+** `len(blocks) == 1` **+** `block is
_region.entry`, the "single-block standalone" shape diag1 banked):

```
python -X utf8 h62.py build --spec=specs/cand_r67_j2.json --dst=j2   -> anchor count 1, head pristine
python -X utf8 h62.py run --arm=j2 --list=synth_r67.txt ...          -> 6/7  [['v3', 43, 42, 2, 23]]
```

The patch is **inert**: repro stays at the landed reading. Frame dump at the detector
(`specs/cand_r67_j2dbg.json`, arm `j2dbg`, stderr only, never lands) shows why — the real
standalone frame is **two** blocks, not one:

```
[J2DBG] cfg=v3 blk=98 blocks_off=[68, 98] blocks_n=2 _reg=IfRegion@98 entry=BasicBlock
        parent=None loop=LoopRegion cond_is_blk=True entry_is_blk=True
```

So `len(blocks)==1` is false at the defect site (diag1's `blocks=[98]` capture was partial: the
frame carries `[loop-tail-block, enclosing-if merge block]`), and `block is _region.entry` is
true everywhere and narrows nothing on its own.

## STEP D — where J1's guard actually fires (arm `j1dbg` = J1's 3 conjuncts + a stderr print)

Whole-corpus hit inventory for the four gate lists (every hit = a frame where J1 fires):

| site | frame reading | effect |
|---|---|---|
| synth `v3` | `blocks=[68,98]`, `R=IfRegion e=98 cb=98 mb=None x=None nb=5 then=[102] else=[106,148,176] par=None`, `L=LoopRegion e=20` | **defect, must fire** |
| synth `v4` | `blocks=[66,80]`, `R=IfRegion e=80 cb=80 mb=None x=None nb=3 then=[84] else=[88] par=None` | passes either way (harmless) |
| `trade_live_broker::get_all_orders` | `blocks=[332,362]`, `R=IfRegion e=362 cb=362 mb=None x=None nb=5 then=[366] else=[370,422,450] par=None`, `L=LoopRegion e=228` | **defect, must fire** — isomorphic to `v3` |
| `quotation::get_trend` | `blocks=[158,206]`, `R=IfRegion e=206 cb=206 mb=220 x=220 nb=2 then=[210] else=[] par=None`, `L=LoopRegion e=84` | **the collateral hit that moves the canary sha — must NOT fire** |

Two readings that correct diag1's rejection note, measured here:
* this tracer arm (J1 semantics + prints only, no state change) does **not** ERR the named
  target: it reads `108/119` with `get_all_orders` cleared. So the ERR is not reproducible at
  J1 semantics in my dir; J1 is nevertheless dead on the canary gate.
* the tracer arm reproduces J1's other two readings exactly: synth **7/7**, canary
  `quotation.pyc` 143/143 but sha **`3eb76e512df9ab1e`** (landed `4d41187e356544e0`) = MOVED.

**The discriminator is in `_region`'s own fields**: every site that must fire has
`merge_block is None ∧ exit is None` (a top-level region that is the *tail* segment of the
function's statement sequence); the one site that must not fire has `merge_block = exit = 220`.

## STEP E — the landed predicate: arm `j3` (specs/cand_r67_j3.json)

Six conjuncts, all read off the current frame's own arguments, `_region`'s own fields and
`self._current_loop`'s own fields — no other region's `blocks` is scanned, no names/offsets/
thresholds, no new `self` state, nothing suppressed (the region returns to the L1754 top-level
owner and is emitted once):

```python
if (region is None and self._current_loop is not None            # frame arg + stack context
        and getattr(_region, 'parent', None) is None              # _region own field
        and block is _region.entry                                # _region own field
        and getattr(_region, 'merge_block', None) is None         # _region own field
        and getattr(_region, 'exit', None) is None):              # _region own field
    continue                                                      # do not claim at this level
```

Arm `j3b` (specs/cand_r67_j3b.json) = the same guard **without** the `self._current_loop`
conjunct (a strictly wider hit surface; own arm, own tally below).

## STEP F — the four gates, all measured in this dir (A/B = `h62.py ab`, landed vs arm)

| gate | landed (re-run here) | **j3** | j3b |
|---|---|---|---|
| repro `synth_r67.txt` | 6/7, `v3 43/42 j2 t23` | **IMPROVED 6/7 → 7/7**, `TALLY SAME=0 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0` | IMPROVED 6/7 → 7/7 (same tally) |
| named target `targets.txt` | 107/119 | **IMPROVED 107/119 → 108/119, no ERR**; `get_all_orders` **absent from the mismatch list = cleared**; the other 11 rows byte-for-byte unchanged | IMPROVED 107/119 → 108/119, `get_all_orders` cleared |
| battery (31) | 115/127, 12 defect funcs | **SAME=31 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0** (115/127, 12 defects, 24 files fully matched both sides) — nothing worsens | SAME=31, nothing worsens |
| canary (4) | 4 brief shas | **SAME=4 / byte-identical**: `4d41187e356544e0`, `af77224b34b203c4`, `e711b8ea86d49a15`, `9d09af09249da177` | SAME=4 byte-identical |

Dumps: `dump/{landed,j3,j3b}_{synth,targets,battery,canary}.jsonl`. All four hard gates **pass**
at `j3` (and at `j3b`).

## STEP G — 16-partial list (copy of `center/all16.txt` -> `fix1/all16.txt`), A/B vs `center/dump/landed16.jsonl`

Baseline read back from the centre file (reproduces the brief): matched **593/641**, **48** defect
functions, Σ|Δ| **328**, Σjumpdiff **184**, Σtruediff **9405**.

Arm `j3` (`dump/j3_all16.jsonl`, run in 4 shards): **SAME=14 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0**

| aggregate | landed | j3 |
|---|---|---|
| matched functions | 593/641 | **594/641** |
| defect functions | 48 | **47** |
| Σ\|Δ\| | 328 | **327** |
| Σjumpdiff | 184 | **182** |
| Σtruediff | 9405 | **9381** |

* `IMPROVED` — `trade_live_broker.pyc` 107/119 → 108/119 (`get_all_orders` cleared).
* `MOVED` — `site-packages/fly/data/quote.pyc` (70/81 both sides, **mismatch rows identical**):
  product text differs, and the difference is the same family working as intended —
  `while self.subscribe.isSet():` + its two `if len(...) > 0:` bodies move **out** of the
  enclosing `for item in futureSids:` / inner block to the function statement sequence, and the
  trailing `return None` appears at function level. Count ruler unchanged (no REGRESSION).
* Everything else byte-identical, no ERR.

## STEP H — controls, variant comparison, re-certification

**(1) J1 re-measured in this dir with diag1's own spec** (`specs/cand_r67_j1.json`, arm `j1`,
`dump/j1_{targets,canary}.jsonl`): targets **108/119 with `get_all_orders` cleared and NO ERR**;
canary `TALLY SAME=3 MOVED=1` (`quotation.pyc` 143/143, sha `3eb76e512df9ab1e` ≠ landed
`4d41187e356544e0`). => J1's disqualifying hard gate is reproducible; the ERR reading is **not**
reproducible here (it behaved exactly like the tracer arm). J1 stays rejected on the canary.

**(2) `j3` vs `j3b`** (with / without the `self._current_loop` conjunct) — byte-identical on
**every** measured item: synth SAME=1, targets SAME=1, canary SAME=4, battery SAME=31,
16-partial SAME=16. So conjunct (2) does no work on the 53 measured items, but it *narrows* the
unmeasured (402-corpus) surface, so the narrower arm **`j3` is the one to land**.

**(3) Final-arm re-certification** — the shipped comment text was corrected afterwards
(comment-only, +3 lines); arm `j3` was rebuilt from `specs/cand_r67_j3.json` and all four gates
re-run as `dump/j3final_*`: repro 7/7, targets 108/119, canary 4/4 byte-identical, battery
SAME=31 / 115/127 / 12 defects, and each `j3final` row SAME against the earlier `j3` row
(comment change is inert). Anchor re-asserted `count==1` on landed bytes at every build, and
`h62.py build` prints "head pristine == worktree bytes" each time.

## VERDICT

**候选：J3** (`D:/Temp/opencode/r67gate/fix1/specs/cand_r67_j3.json`, one edit, anchor at
`core/cfg/region_ast_generator.py` L21928-21932, +57 lines = 51 comment + 6 guard, 0 removed).
Four hard gates pass; 16-partial strictly improves (594/641, 47 defects, Σ|Δ|327, Σjd 182,
Σtd 9381) with one benign MOVED. **Recommend landing**, with the 402-file sweep run by the centre
before it is banked (my arm can only fire where J1 fired, minus the `merge/exit` and non-entry
shapes).

Two corrections handed back to the centre/diag record:
* the banked "standalone `blocks` is a single block" narrowing is **false** (2 blocks at every
  hit) — a patch built on it is inert (arm `j2` measured: repro stays 6/7);
* J1's target ERR is **not reproducible**; J1 is rejected by the canary sha alone.

Provisioning hazard worth fixing centrally: the `fix1` copies of `h62.py`/`cstrict.py` still
pointed at `r67gate/diag1`, so a fix-workspace run would have written mirrors/builds/dumps into a
diagnose agent's live directory. Retargeted here; the same literal is presumably still wrong in
any other fix dir provisioned this round.

Repo `F:/Downloads/pythoncdc-main` untouched throughout (no writes to `core/`, `*OK.py`,
`pyc_index.json`, `.trae/`, `test_repros/`); `git status --short core/` empty before and after;
siblings `diag2..diag6` never opened; no 402-file sweep run here.



