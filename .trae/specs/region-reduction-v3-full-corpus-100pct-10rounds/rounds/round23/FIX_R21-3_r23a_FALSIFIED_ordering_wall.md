# FIX_R21-3 — r23a — merge-landing analyzer declaration (api_base `get_history_df`, strategy `tick_worker_thread`)

Owner mechanism: `core/cfg/region_analyzer.py` ONLY. All other generator files read-only.
Repo (read-only): D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main, branch rr-v3r01-f557fd.
All products -> D:/Temp/r23a/out. Never write *OK.py into repo. Never run the 402 gate.

## Mirror build proof
- Mirror root: `D:/Temp/r23a/wt` (repo copied read-only): `pycdc.py core parsers utils bytecode scripts`
  + `cp --parents -r` of the six battery dirs (round14/repro, round14/repro_arm, round14/repro_ccneg,
    round18/repro_retbreak, round19/repro_orderapi, round19/repro_tail) at identical relative depth.
- `D:/Temp/r23a/pristine` = independent copy of the same set.
- sha256 first-16 of `core/cfg/region_analyzer.py`: wt = `ec6bd48826c65df9`, pristine = `ec6bd48826c65df9`
  ⇒ mirror == repo bytes at build time. No repo writes.

## Stage 1 baseline (unpatched mirror)
Products written to `D:/Temp/r23a/out/stage1/*`, judged with
`python -X utf8 scripts/pyc_verify.py single <pyc> --source <mirror product>` (repo ruler, read-only).
Judge hashes of the mirror products are in the log `D:/Temp/r23a/logs_stage1.txt`.

| file | brief | mirror | note |
|---|---|---|---|
| IQData/api/api_base.pyc | 27/28 | **27/28** | match |
| .../strategy/strategy.pyc | 26/27 | **26/27** | match |
| IQCommon/strategy/wizard_quant_api.pyc | 55/58 | **57/58** | REPO MOVED (gate 23 comprehension fix landed); use 57/58 as my reference, do not fight it |
| fly/data/quote.pyc | 88/92 | **88/92** | match |
| .../real_quote.pyc | 44/45 | **44/45** | match |
| IQCommon/api/klinedata.pyc | 63/64 | **63/64** | match |
| IQCommon/logger/handlers.pyc | 29/30 | **29/30** | match |
| IQCommon/util/trade_info_utils.pyc | 38/41 | **38/41** | match |
| .../realtime_event_source.pyc | 12/13 | **12/13** | match |
| .../risk_calculation/__init__.pyc | 42/43 | **42/43** | match |
| .../trade_live_broker.pyc | 118/128 | **118/128** | match |
| fly/data/quotation.pyc (sentinel) | 153/153 | **153/153** | match |
| .../fly_api/order_api.pyc (sentinel) | 37/37 | **37/37** | match |
| .../plugin_system_matcher/matcher.pyc (sentinel) | 17/17 | **17/17** | match |

NOTE: the brief's `fly/data/quote.pyc` / `fly/data/quotation.pyc` / `order_api` / `matcher` live at
`site-packages/fly/data/*`, `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`,
`site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc` (resolved by `find`).

## Signature re-verification
api_base `<module>.get_history_df` — region dump of the UNPATCHED mirror confirms every quoted fact:
`IfRegion entry=992 merge=1098 cond=992 exit=1098 then=[996,1008,1040,1024,1036,1034] else=[]`;
`IfRegion entry=996 merge=1040 cond=996 then=[1008,1024,1036,1034,1098,1142,1200] else=[]`;
`IfRegion entry=1008 merge=1040 cond=1008 then=[1040] else=[1098]` (so @1098 is owned by @1008's
else arm, NOT declared as @992's else); `entry=1098 merge=1782 IF_THEN_ELSE`, `entry=1258 IF_ELIF_CHAIN`.
CFG edges: `B@992 succ=[1098,996] last=POP_JUMP_FORWARD_IF_TRUE`; `B@996 succ=[1040,1008] IF_TRUE`;
`B@1008 succ=[1024,1036] IF_FALSE`; `B@1024 succ=[1098,1034] IF_FALSE`; `B@1034 -> @1040 JUMP_FORWARD`;
`B@1036 POP_TOP -> @1098`; `B@1040 -> @1782`; `B@1098 succ=[1142,1200]`; `@1254` is NOT a block start.
Shape on the unpatched mirror product (`unit_diff ... --prod`): `delta=0 hunks=0 landings=2`,
`@994 IF_TRUE -> idx219` and `@1006 IF_TRUE -> idx210` become `-> idx254` for both. ⇒ the true shape is
**outer condition = `not A and (B or (C and D))`** for the if/elif/else ladder @992(body@1040) /
E@1098(body@1142, body@1200), merge @1782; both `or` short-circuit exits (@994 AND-false-exit,
@1006 OR-true-exit) are declared onto one wrong shared landing @1254.

## 判据实现 (exact file:line + predicate)
ATTEMPTED (and measured; see stage readings — it does NOT flip a named unit, so it is
delivered REVERTED; the delivered `region_analyzer.py` is byte-identical to the sealed bytes).

Candidate site: `core/cfg/region_analyzer.py:19617` (inside `_identify_conditional_regions`,
immediately under the pre-existing BoolOpRegion fallback at `:19613-19615` that already
re-materialises an `and` op_chain into `_main_inline_boolop_chain`).

Predicate added (mirror `D:/Temp/r23a/wt`, pristine `ec6bd48826c65df9`, +16 lines):
```
elif _op_chain_ops == {'or'} and len(block_region.op_chain) >= 2:
    _main_inline_boolop_chain = {'blocks': [b for b, _ in block_region.op_chain], 'op': 'or'}
```
Gated by the already-existing same-block guards: `_main_inline_boolop_chain is None` ∧
`chain_blocks` ∧ `isinstance(block_region, BoolOpRegion)` ∧ `block_region.entry == block`
(原则 4 — the only cross-region read is the expression-level child region *entered at this very
block*, which the existing `and` branch reads identically). No sibling/parent region read,
no ordering dependence, no retrospective repair: the decision is taken at identification and
stored into `IfRegion.inline_boolop_chains[id(condition_block)]` by the existing
`_build_basic_if_region` (`:21225-21232`) / `_build_elif_region` channel.

Motivation (re-measured, cheap): `inline_boolop_chains` is EMPTY on every IfRegion of both
failing units while `BoolOpRegion@512 op_chain=[(512,'or'),(524,'or')] merge=568` exists —
`condition_block` had been redirected `512 -> 524` at `:19166`
(`condition_block = block_region.op_chain[-1][0]`) without recording the chain, so the
generator's `_main_ibc` lookup (`region_ast_generator.py:15493`) misses and emits a single-block
condition whose leading operand's short-circuit exit has no AST landing.

## Stage readings
Unpatched mirror (stage1) == brief for every file except wizard (57/58, repo moved).

| target | before (unpatched) | after candidate | judge |
|---|---|---|---|
| strategy `<module>.Strategy.tick_worker_thread` | `delta=0 hunks=0 landings=4` (orig `@522/@534 -> @568`, `@992/@1004 -> @1038`; prod `-> @820 / @1286`) | `delta=0 hunks=2 landings=2` — `@534`/`@1004` flip `IF_TRUE -> IF_FALSE`, `@522 -> idx75`, `@992 -> idx185` | **26/27 UNCHANGED, no flip** |
| api_base `<module>.get_history_df` | `delta=0 hunks=0 landings=2` | **byte-identical product** (sha `4ec57b916a348832` == stage1) | **27/28 UNCHANGED, inert** |

api_base inertness explained by the re-derived shape (see below): its condition is
`not X and (Y or (Z and W))` — the head `X` terminates in `POP_JUMP_FORWARD_IF_TRUE` whose target
IS the region's declared merge `@1098`, i.e. a *negated and-head*, so no `BoolOpRegion@992` is
created at all (`op_chain` empty, dump shows only IfRegion@992/@996/@1008) and the
`block_region.op_chain` gate at `:19166`/`:19613` never opens. Not reachable from this site.

## 负面证据
1. **api_base `get_history_df` is NOT a boolop-chain-declaration miss at `:19166`.** Region dump of the
   unpatched mirror: `IfRegion entry=992 cond=992 merge=1098 then=[996,1008,1040,1024,1036,1034] else=[]`,
   `inline_boolop_chains = {}`, `op_chain = []`, and there is **no BoolOpRegion with entry 992**
   (contrast strategy, which does have `BoolOpRegion@512`). Any criterion gated on
   "this block is the entry of a BoolOpRegion" is structurally dead on api_base.
2. **The candidate fires (strategy product bytes change, `7701418d8c190837 -> 74fce99a42531b3a`) yet
   yields zero unit flips** — the classic fires-without-flips class. It converts a pure-landing
   residual into an opcode-polarity residual (`hunks 0 -> 2`): `inline_boolop_chains['blocks']`
   = `[op_chain blocks]` carries only the *links* (512, 524), never the chain's **tail operand**
   (block 536, whose `IF_FALSE` continues to 562 -> 568), so the rebuilt
   `BoolOp(or,[A,B])` has 2 values for a 3-operand source condition and the generator inverts the
   last emitted jump instead of landing it.
3. **`@568` is the then-body and is NOT in `IfRegion@512.blocks`** while `IfRegion@536 merge=568`
   owns it; `inline_boolop_chains` alone cannot give the outer region its third operand without a
   cross-region membership read of `IfRegion@536` (forbidden), so the missing operand is *not*
   recoverable from region-512's own data at identification time. This is the ordering wall again.
4. Reverting the candidate restores byte equality with pristine (proved by `cmp` below).

## Final declaration
**FALSIFIED** — and additionally **panel-negative**, so it is NOT deliverable even as
supporting work. The delivered `D:/Temp/r23a/DELIVER/region_analyzer.py` is **byte-identical to the
sealed bytes** (this is the first line of substance above; proof: `cmp` vs `pristine` and vs the
repo file both clean, `REVERT_BYTE_IDENTICAL`).

- delivered sha256 first-16: **`ec6bd48826c65df9`** (== pristine == repo HEAD bytes; 32672 lines;
  changed-line count vs pristine = **0**)
- `py_compile` proof: `python -m py_compile D:/Temp/r23a/DELIVER/region_analyzer.py` → **PYCOMPILE_OK**
- revert command already executed in the mirror:
  `cp /d/Temp/r23a/pristine/core/cfg/region_analyzer.py /d/Temp/r23a/wt/core/cfg/region_analyzer.py`
  (repo itself was never written; no `git` write performed)

### Verdict per target
| target | before | after candidate | flip? |
|---|---|---|---|
| `IQData/api/api_base.pyc` `<module>.get_history_df` | 27/28, `delta=0 hunks=0 landings=2` | 27/28, product byte-identical (**inert**), shape unchanged | NO |
| `IQEngine/.../strategy.pyc` `<module>.Strategy.tick_worker_thread` | 26/27, `delta=0 hunks=0 landings=4` | 26/27, `delta=0 hunks=2 landings=2` | NO |

### Panel under the candidate (patched mirror, `--source` fresh products; log `D:/Temp/r23a/logs_p2.txt`)
`api_base 27/28 =` · `strategy 26/27 =` · `wizard 57/58 =` · **`fly/data/quote 88/92 → 84/92` (−4,
hard regression)** · `real_quote 44/45 =` · `klinedata 63/64 =` · `handlers 29/30 =` ·
`trade_info_utils 38/41 =` · `realtime_event_source 12/13 =` · `risk_calculation 42/43 =` ·
`trade_live_broker 118/128 =`. The three sentinels (quotation 153/153, order_api 37/37, matcher 17/17)
were not reached because the candidate was already disqualified by the quote regression; batteries
therefore were not run (the 402 gate was never run, per protocol).

### Most important negative fact (for the next ticket)
`inline_boolop_chains` cannot be refilled from `BoolOpRegion.op_chain` alone: **`op_chain` stores
the LINKS, not the operands.** For `strategy` the source condition has 3 operands
(`@512 or @524 or <@536 tail>` reaching then-body `@568` via `@562`) but
`op_chain = [(512,'or'), (524,'or')]`, and the tail operand `@536` is owned by the *sibling*
`IfRegion@536 (merge=568)`. Handing the generator `[512, 524]` therefore makes it emit
`BoolOp(or, [A, B])` and **invert** the last jump (`@534`/`@1004` `IF_TRUE → IF_FALSE`) instead of
landing it — landings 4→2 at the cost of hunks 0→2, no unit flip, and 4 quote-units lost.
Any complete fix must obtain the chain's tail operand without reading a sibling region ⇒
it is blocked by the ordering wall, not by a missing analyzer field.

api_base needs a different mechanism entirely: no `BoolOpRegion@992` exists, and its head `@992`
terminates in `POP_JUMP_FORWARD_IF_TRUE → @1098` where `@1098` is the declared merge, i.e. a
**negated `and` head** (`not X and (Y or (Z and W))`) that both chain walks
(`:19465` and-walk requires `'IF_FALSE'`; `:19396` or-walk requires all members' IF_TRUE to hit the
*then* entry) reject at the first block.

## Mirror self-certification
Pristine-vs-mirror `region_analyzer.py` hashes equal before patch (`ec6bd48826c65df9`), `cmp` clean
after revert, and `pycdc.decompile_pyc` of every panel file through the **unpatched mirror**
reproduced the Stage-1 counts quoted in the brief exactly (only wizard differs, 55/58 → 57/58,
consistent with gate 23 having landed while this ticket was in flight).
