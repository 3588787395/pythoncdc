# FIX_R21-6 — r24b — refuse the elif fold of a merge-less IF_ELIF_CHAIN whose arms do not converge

Mechanism owned: `core/cfg/region_analyzer.py` ONLY. Single mechanism: at identification time,
REFUSE the flat `IF_ELIF_CHAIN` reading of a region whose `merge` declaration is genuinely missing
AND whose own arms jump forward to two different outside blocks — the shape that hides a nested
sub-chain plus its trailing statements inside the else side.
Victim: `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
unit `<module>.TradeLiveBroker.rzrq_credit_order` (`hunks=0 landings=1`, `@2368 JUMP_FORWARD`
lands on `orig->idx490` vs `prod->idx485`).
`region_ast_generator.py`, `ast_generator_v2.py`, `comprehension_generator.py` were not read or
patched by this ticket (only sha-copied into the mirror so the pipeline runs; every measurement that
could depend on them was taken against the landed bytes).

## Mirror build proof
Mirror root `D:/Temp/r24b/wt`. Copied `pycdc.py core parsers utils bytecode scripts site-packages`
(32M) + the six battery dirs at identical relative depth + `unit_diff.py` (sha16
`2d9161f41fc8ae9f`, committed, `--all` wired). sha256 first-16 of copied core files, mirror vs repo —
all equal: `pycdc.py cf4e2705ab042732`, `region_analyzer.py ec6bd48826c65df9`,
`region_ast_generator.py 4f295dfc6ebd2caa`, `comprehension_generator.py 7d8acab92ccc7782`,
`ast_generator_v2.py beeaf14435e22922`. Pristine kept at `D:/Temp/r24b/pristine/region_analyzer.py`
(`ec6bd48826c65df9`).
Self-certification: `python -X utf8 pycdc.py --region site-packages/fly/data/quotation.pyc -o
D:/Temp/r24b/out/quotation_mirror.py` → `cmp` against the repo's committed
`site-packages/fly/data/quotationOK.py` → **byte-identical**. All products go to `D:/Temp/r24b/out`
only (`panel.py` names them `<rel>_s1.py` / `<rel>_p1.py`); no `*OK.py` written anywhere; batteries
run with `TMPDIR/TMP/TEMP=D:/Temp/r24b/out`. No `git` write of any kind.

## Stage 1 baseline (UNPATCHED mirror; judge = `pyc_verify single --source <fresh product>`)
Reproduced every recorded value exactly:

| file | measured | expected |
|---|---|---|
| trade_live_broker.pyc | 118/128 | 118/128 |
| fly/data/quote.pyc | 88/92 | 88/92 |
| wizard_quant_api.pyc | 57/58 | 57/58 |
| real_quote.pyc | 44/45 | 44/45 |
| klinedata.pyc | 63/64 | 63/64 |
| handlers.pyc | 29/30 | 29/30 |
| trade_info_utils.pyc | 38/41 | 38/41 |
| IQData/api/api_base.pyc | 27/28 | 27/28 |
| fly_data/strategy/strategy.pyc | 26/27 | 26/27 |
| realtime_event_source.pyc | 12/13 | 12/13 |
| plugin_system_risk_calculation/__init__.pyc | 42/43 | 42/43 |
| fly/data/quotation.pyc | 153/153 | 153/153 |
| matcher.pyc | 17/17 | 17/17 |
| order_api.pyc | 37/37 | 37/37 |

Batteries (unpatched): repro **RED=9/9** · arm **GREEN=0 RED=3/3** · ccneg **GREEN=3 RED=1/4** ·
retbreak **GREEN=2 RED=2, DRIFT_VS_BASELINE=0/4** · orderapi **GREEN=5 RED=0/5** · tail
**GREEN=13 RED=0/13** — all at recorded values.

## Signature census (before any predicate)
Rig corrections found while building it: klinedata's unit is module-level
`<module>.get_kline_by_count_new` (no class segment); real_quote's
`<module>.RealQuoteData.get_tick_direction` is now **`hunks=0 landings=0 judge_diff=False`** — it
already flipped (that is the recorded 44/45), so it is a *negative* member of this census, not a
target. See 负面证据 §5 for the `unit_diff.py` mirror hazard.

Measured shapes (`unit_diff --all --prod <fresh s1 product>`):

| unit | len orig/prod | delta | hunks | landings | jumping instruction | orig landing | prod landing |
|---|---|---|---|---|---|---|---|
| broker `rzrq_credit_order` | 780/780 | 0 | 0 | 1 | `@2368 JUMP_FORWARD` | idx490 = **@2534** | idx485 = @2506 |
| broker `get_ipo_stocks` | 481/481 | 0 | 0 | 1 | `@1108 POP_JUMP_FORWARD_IF_TRUE` | idx225 = @1154 | idx215 = @1130 |
| broker `_process_tick_order` | 182/182 | 0 | 0 | 1 | `@178 JUMP_BACKWARD` | idx22 | idx19 |
| broker `etf_basket_order` | 756/756 | 0 | 2 | 1 | `@672 POP_JUMP_FORWARD_IF_FALSE` | idx271(@1328) | idx508(@2452) |
| klinedata `get_kline_by_count_new` | 642 instrs, 1 merge-less CHAIN | – | – | – | (arm tails all backward) | – | – |
| real_quote `get_tick_direction` | 295/295 | 0 | 0 | 0 | — | — | — (already Equal) |

Per-unit region census (out-of-band: `build_cfg(code_obj)` + `RegionAnalyzer(cfg).analyze()` → the
region LIST, read AFTER `analyze()` returns so no in-analyzer probe can perturb a product; script
`D:/Temp/r24b/census2.py`, dumps in `D:/Temp/r24b/out/census_broker.txt`, `census_kline.txt`,
`census_rq.txt`):

| unit | IfRegions | merge-less (all types) | merge-less **IF_ELIF_CHAIN** | arm tails jumping OUTSIDE the region | distinct external targets | does an arm's jump target equal the original's landing? |
|---|---|---|---|---|---|---|
| broker `rzrq_credit_order` | 25 | 3 | **1** (`entry=2136 cond=2136 then=[2148] else=[2192,2204,2370,2216,2254,2382,2420,2340,2266,2304,2432,2470]`, arms end `2148[RETURN_VALUE] 2340[JUMP_FORWARD→2534] 2382/2432[JUMP_FORWARD→2506] 2470[STORE_FAST]`) | 6 (`2340→2534`, `2382→2506`, `2432→2506` + body mirrors) | **2**: {2506, 2534} | **YES** — 2534 = idx490 = orig landing; 2506 = idx485 = prod landing |
| broker `get_ipo_stocks` | 23 | 2 | **0** (both are IF_THEN/IF_THEN_ELSE) | yes (590/928→968) on a non-chain region | – | NO — `@1108` lands on **@1154**, a *declared* merge of another region (r23d's "correctly declared merge=1154 lost to if/elif fusion in the printed source") |
| broker `_process_tick_order` | 3 | **0** | **0** | none | – | NO — the diff is a `JUMP_BACKWARD` (`@178 →idx22` vs `idx19`), loop-entry mechanism |
| broker `etf_basket_order` | 42 | 4 | **1** (`entry=484 cond=484 then=[510] else=[554,558,564]`) | 1 (`558→568`) **plus a BACKWARD arm tail** (`then@510 JUMP_BACKWARD→480`) | 1 | NO — its diff is `@672 →idx271(@1328)` vs `idx508(@2452)` with **2 hunks of 11 moved instructions** (territory, not landing) |
| klinedata `get_kline_by_count_new` | 21 | 1 | **1** (`entry=0 cond=80`) | **0 external forward tails**; 15 BACKWARD tails (`then@134`, `else@252`, …) | 0 | NO — backward-arm family |
| real_quote `get_tick_direction` | – | – | – | – | – | **unit is already Equal**: `delta=0 hunks=0 landings=0 judge_diff=False` (the gate-22 flip behind 44/45), so it cannot be a member of this census |

**Headline counts.** `IF_ELIF_CHAIN ∧ merge_block is None` = **3 of the 6 named units** (rzrq, etf,
klinedata). The *actionable* signature — that merge-less chain owning a forward arm tail whose
external landing set has **two distinct blocks** (the chain exit 2534 and the nested sub-chain's own
convergence 2506), one of them being the original's landing = **1 of 6: `rzrq_credit_order` only**.
The census therefore does NOT license a family criterion; it licenses exactly one unit, which is the
named bar, and it supplies the two discriminators that keep etf and klinedata out.

Mechanical reading of the victim (all from the region's own data, no sibling read):
`chain@2136` flattens `elif_conditions=[2192,2370,2420]`, `bodies=[[2204..2304],[2382],[2432]]`,
`final_else=[2470]`, `merge=None`. The nested sub-chain entered at 2370 converges at **2506**, and
block 2506 is NOT one of this region's blocks, so the emitted source hoists
`entrust_direction = EntrustDirection.BUY; entrust_bs = '1'` to after the whole chain; the
`elif`-arm tail `@2368 JUMP_FORWARD` therefore lands there (idx485) instead of at the chain's real
exit 2534 (idx490). The sink then-arm (`2148 RETURN_VALUE`) is why post-dominator analysis yields
`merge=None`, and the existing `_chain_merge_candidates` machinery (arm-end successor intersection,
pristine `:22621-22759`) cannot recover it either: body0 leaves through `2340→2534` while body1 and
body2 leave through `2506`, so the intersection is empty and merge stays `None`.

## 判据实现
File: `core/cfg/region_analyzer.py` ONLY. One site, inside `_build_elif_region` (`def` at `:21242`),
immediately after `elif_info = _check_elif_chain(block, else_blocks, merge)` (`:22572`) and its
`if elif_info is None: return None` guard — i.e. at identification time, before the region object is
constructed (pristine `:22854` → patched `:22918`).

* Comment block: **`region_analyzer.py:22575-22599`**.
* Predicate code: **`region_analyzer.py:22600-22637`**, refusal at **`:22635-22637`**.

```python
if merge is None:                                                   # :22600
    _r24b_own = {start offsets of block, then_blocks, elif conditions,
                 elif bodies, elif final_else}                      # :22601-22610
    _r24b_arms = [then_blocks] + elif_bodies + [elif_final_else]    # :22611-22614
    _r24b_has_sink = False; _r24b_exit_sets = []                    # :22615-22616
    for _r24b_arm in _r24b_arms:                                    # :22617
        for _r24b_b in _r24b_arm:
            _r24b_li = _r24b_b.get_last_instruction()
            if _r24b_li.opname in ('RETURN_VALUE','RETURN_CONST','RAISE_VARARGS','RERAISE'):
                _r24b_has_sink = True; continue                     # :22623-22626
            if _r24b_li.opname in ('JUMP_FORWARD','JUMP_ABSOLUTE') or FORWARD_CONDITIONAL_JUMP_OPS:
                if _r24b_li.argval not in _r24b_own:
                    _r24b_exits.add(_r24b_li.argval)                # :22627-22632
        if _r24b_exits: _r24b_exit_sets.append(_r24b_exits)         # :22633-22634
    if (_r24b_has_sink and len(_r24b_exit_sets) >= 2                # :22635-22636
            and any(_r24b_s != _r24b_exit_sets[0] for _r24b_s in _r24b_exit_sets)):
        return None                                                 # :22637
```

Three conjuncts, every input from **this region's own** `then_blocks` /
`elif_info["conditions"|"bodies"|"final_else"]` block tables plus each block's own last instruction
(`opname`, `argval` only):
① `merge is None` — the declaration is genuinely missing; nothing existing is re-bound and no
retrospective repair happens.
② Some arm is a sink (`RETURN_VALUE`/`RETURN_CONST`/`RAISE_VARARGS`/`RERAISE`) — the reason
post-dominator analysis returned `None`, and the discriminator against etf_basket_order's merge-less
chain@484 (no sink arm; its then arm ends `JUMP_BACKWARD→480`).
③ At least two arms leave the region by **forward** jumps and their landing sets are **not all
equal** — a flat elif chain has exactly one exit, so two distinct landings mean the earlier one is a
nested sub-chain's own convergence with trailing statements after it, and the fold must be refused.
klinedata's chain@0 has zero forward exits (15 backward) and etf@484 has a single exit set `{568}` →
neither fires.
No `block.successors`, no `get_block_by_offset`, no sibling/parent region read, no name/constant
read, no absolute-offset or instruction-count constant, no dependence on region processing order
(one-way, upward dataflow only). `return None` reuses the existing fallback
`_build_basic_if_region` (`:20675-20680`) → `IF_THEN_ELSE`: the nested sub-chain stays its own
abstract `IfRegion` node (principle 3), the block at 2506 and its trailing statements remain inside
the else-side suite (principle 2), one region type → one AST node type, no new node type, no
cross-level back-fill.
Diff vs pristine: **+64 lines / −0**, one contiguous block, `32672 → 32736` lines. `patch_r24b.py`
(`D:/Temp/r24b/patch_r24b.py`) anchors on line index 22571 AND content, rebuilds with
`splitlines(True)` and asserts the file's uniform CRLF (32672 CRLF / 0 bare LF).

## stage readings
Victim and the other named broker units (`unit_diff --all`, patched product
`D:/Temp/r24b/out/broker_p1.py`):

| unit | before | after |
|---|---|---|
| `rzrq_credit_order` | `delta=0 hunks=0 landings=1 judge_diff=True` (`@2368 JUMP_FORWARD → idx485` vs `idx490`) | **`delta=0 hunks=0 landings=0 judge_diff=False`** |
| `get_ipo_stocks` | `delta=0 hunks=0 landings=1` | unchanged (still red) |
| `_process_tick_order` | `delta=0 hunks=0 landings=1` | unchanged (still red) |
| `etf_basket_order` | `delta=0 hunks=2 landings=1` | unchanged (still red) |

Panel after patch (judge = `pyc_verify single --source <fresh product>`, products
`D:/Temp/r24b/out/*_p1.py`): broker **118/128 → 119/128** (the named flip), klinedata 63/64,
real_quote 44/45, quote 88/92, wizard 57/58, handlers 29/30, trade_info_utils 38/41, api_base 27/28,
strategy 26/27, realtime_event_source 12/13, risk_calculation 42/43 — **zero decreases**; sentinels
matcher **17/17**, order_api **37/37**, quotation **153/153** all hold on their patched products.

Batteries on the patched mirror (all six at recorded values; run from the mirror root with
`TMPDIR/TMP/TEMP=D:/Temp/r24b/out`): repro **RED=9/9** · arm **GREEN=0 RED=3/3** · ccneg
**GREEN=3 RED=1/4** · retbreak **GREEN=2 RED=2, DRIFT_VS_BASELINE=0/4** · orderapi
**GREEN=5 RED=0/5** · tail **GREEN=13 RED=0/13**.

Fire census over the whole 14-file panel (`D:/Temp/r24b/census3.py`, the predicate evaluated
out-of-band against the PRISTINE analyzer for every code object, so each hit is one refusal the patch
causes): broker **fires=1** = `('rzrq_credit_order', entry=2136, exits=[2506, 2534])` — exactly the
named unit — and `klinedata 0 · real_quote 0 · quote 0 · wizard 0 · handlers 0 · trade_info_utils 0 ·
api_base 0 · strategy 0 · realtime_event_source 0 · risk_calculation 0 · matcher 0 · order_api 0 ·
quotation 0` ⇒ **TOTAL_FIRES = 1 on the entire panel**, which is why no other panel number moved.

## 负面证据
1. **The signature is NOT a family.** `IF_ELIF_CHAIN ∧ merge_block is None` = 3 of the 6 census
   units, but the actionable variant = **1 of 6 (`rzrq_credit_order` only)**. etf's chain@484 has one
   exit set `{568}` and no sink arm; klinedata's chain@0 has 15 backward arm tails and **zero**
   external forward tails; `get_ipo_stocks` has 0 merge-less chains (its `@1108` lands on `@1154`, a
   *declared* merge — the closed generator axis); `_process_tick_order` has 0 merge-less IfRegions at
   all (loop-entry axis). The "one merge criterion covers the family" assumption stays refuted, and
   the `op_chain`-stores-links-not-operands axis (strategy's chain tail) was not reopened.
2. **`real_quote.get_tick_direction` is no longer a census member** — `delta=0 hunks=0 landings=0
   judge_diff=False` on the fresh s1 product; it is the gate-22 flip behind the recorded 44/45. Any
   brief premised on it being open is stale.
3. Declaring only the later landing (`merge=2534`) without refusing the fold is not an available
   mechanism here: the generator has no landing channel (AST carries no jump operands), so the only
   correct-at-identification move is the taken one — refuse the fold so the trailing block stays in
   the else-side suite and the landing becomes emergent. Verified: the refusal alone moved the
   landing from idx485 to idx490 with `hunks=0 delta=0` unchanged.
4. Broker still needs its other mechanisms to close the FILE: **119/128, 9 units red. No file-level
   progress is claimed.** The other three broker units measured kept their exact shapes.
5. Tooling hazards recorded so they are not re-paid: (a) `unit_diff.py` is NOT inside the six
   battery dirs — a mirror copied without it dies with `can't open file ... unit_diff.py` for every
   unit, which reads deceptively like "this unit has no content diff"; copied it to the same relative
   depth (sha16 `2d9161f41fc8ae9f`) before any shape reading. (b) My own first revert helper contained
   a dead `while …: pass` loop that spun for minutes (killed by PID 9296; the patched bytes were
   already saved, and the revert path was afterwards proven byte-exact against `pristine/`). Note a
   gate (`gate_chain.py 24 23`) and other engineers' regen shards were running on this machine
   throughout — the spinning process made several unrelated commands look slow; no repo file, product
   or gate run was touched by this ticket.

## final declaration
**LANDED-READY.**

* Delivered: `D:/Temp/r24b/DELIVER/region_analyzer.py` = the WHOLE changed file (2091407 bytes,
  32736 lines), sha256 first-16 **`b7f3076323813787`**, `cmp`-identical to the mirror file every
  reading above was taken from (`D:/Temp/r24b/wt/core/cfg/region_analyzer.py`).
* Changed lines vs pristine (`ec6bd48826c65df9`): **+64 / −0**, one contiguous block at
  `region_analyzer.py:22575-22638` (comment `22575-22599`, predicate `22600-22637`) inside
  `_build_elif_region`; uniform CRLF preserved and asserted.
* `python -X utf8 -m py_compile` passes on both the mirror file and the delivered file
  (`PY_COMPILE OK both`).
* Bar met: `rzrq_credit_order` judge **Equal** ⇒ `trade_live_broker.pyc` 118/128 → **119/128**, zero
  decreases across the 14-file panel, sentinels 153/153 · 17/17 · 37/37, all six batteries at
  recorded values, and the predicate fires exactly once on the whole panel.
* Revert (either, both proven): `python -X utf8 D:/Temp/r24b/patch_r24b.py
  core/cfg/region_analyzer.py --revert` (anchored on line index 22571 + content; in this run it
  produced a file `cmp`-identical to `D:/Temp/r24b/pristine/region_analyzer.py`), or
  `cp D:/Temp/r24b/pristine/region_analyzer.py core/cfg/region_analyzer.py`.
* Repo untouched by this ticket: no `git` write, no `*OK.py` written into the repo, no 402-file gate
  run; all products under `D:/Temp/r24b/out`. (`git status --short core/` in the repo shows only the
  other engineer's in-flight `region_ast_generator.py`; `region_analyzer.py` is clean there.)
* Closing re-judge from the re-applied delivered bytes (after the revert→re-apply cycle):
  `trade_live_broker.pyc` **119/128** (`out/IQEngine__plugins__plugin_system_trade__trade_live_broker_final.py`),
  i.e. every reading above corresponds to sha16 `b7f3076323813787`.
