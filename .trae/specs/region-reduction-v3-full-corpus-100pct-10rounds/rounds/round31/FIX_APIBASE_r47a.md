# FIX_APIBASE — r47 — api_base.get_history_df (27/28 → 28/28)

Owner file: **`core/cfg/region_ast_generator.py`** (+150 lines / −0, byte-preserved CRLF).
Declaration: **CANDIDATE READY (file flip: `IQData/api/api_base.pyc` 27/28 → 28/28)**.

---

## 0. Ticket as received

Victim: `site-packages/IQData/api/api_base.pyc`, co-name `get_history_df`.
Sealed reading: `len orig=1881 prod=1881 delta=0 hunks=0 landings=2`.
Sealed bytes (sha256|cut -c1-16): `core/cfg/region_ast_generator.py = 7d336164eff5bf65`,
`core/cfg/region_analyzer.py = 35e227ac3e7b25af`.
Predecessor diagnosis (FIX_R21-19_r43a.md) taken as given: the landed `_r2119_or_tail_extension`
needs a BoolOpRegion and api_base's enclosing leg (IfRegion@992) has none; the compile()-decided
target shape is `if not include and (test2 or test3): B` **with** `else: <T chain>` (banked at
`D:/Temp/r37/out/HAND_api_A.py`); rejected variants: T as following sibling ⇒ `delta=−1`;
or-merge only kept nested ⇒ `landings=1`. Required work: an `and`-lift of the enclosing single
`IF_TRUE→tail` leg combined with the or-tail merge. Only the generator may be edited; no
analyzer/ownership changes were made (section 7: none needed).

Acceptance: `get_history_df` reads `delta=0 hunks=0 landings=0 judge_diff=False` AND api_base
reads 28/28, no panel count decreasing.

## 1. Mirror + sealed-hash + cmp proof

Mirror `D:/Temp/r47/wt` = repo copy of `pycdc.py core parsers utils bytecode scripts` +
`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py` at the same relative
depth (no `__pycache__`). `diff -r` of every copied tree against the repo → clean
(`MIRROR_CLEAN`), sealed hashes verified before any edit:

| file | sealed | mirror at start |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `7d336164eff5bf65` | `7d336164eff5bf65` ✅ |
| `core/cfg/region_analyzer.py` | `35e227ac3e7b25af` | `35e227ac3e7b25af` ✅ |

Fidelity proof (pristine mirror, before any patch):
`python -X utf8 pycdc.py <repo>/site-packages/IQData/api/api_base.pyc -o scratch/out/api_baseOK.py`
(delete-first) → `cmp` against the repo's committed `api_baseOK.py` = **IDENTICAL**
(33 228 B, sha16 `fff12a519aee3735`). Mirror valid.

Reproduce-the-bank proof: my `scratch/var_A.py` regenerated from the committed product
differs from `D:/Temp/r37/out/HAND_api_A.py` (CR-normalised) by **nothing**
(`VAR_A_MATCHES_BANKED`), and my patched product `scratch/out/api_base_r47.py` (LF-normalised)
equals `var_A.py` exactly — one hunk only (11 lines ↔ 11 lines), i.e. nothing else moved.

## 2. Baseline

```
$ unit_diff.py <repo>/site-packages/IQData/api/api_base.pyc get_history_df --prod scratch/out/api_baseOK.py --all
len orig=1881 prod=1881 delta=0
   ~ orig[193] @994  POP_JUMP_FORWARD_IF_TRUE ->idx219 | prod[193] @994 ... ->idx254
   ~ orig[197] @1006 POP_JUMP_FORWARD_IF_TRUE ->idx210 | prod[197] @1006 ... ->idx254
hunks=0 landings=2 judge_diff=True
$ pyc_verify single api_base.pyc --source scratch/out/api_baseOK.py
[single] status=failure units=27/28 success_rate=96.43%
```
Both sealed numbers reproduced on the sealed bytes.

## 3. 取证 — region census of IfRegion@992 and the enclosing chain, construction site, compile() table

Own probe `D:/Temp/r47/scratch/probe_r47.py` (out-of-process, imports `D:/Temp/r47/wt`; analyzer
bytes sealed), unit `get_history_df`, offsets 990–1100:

```
IfRegion entry=992  cond=992  merge=1098 then=[996,1008,1040,1024,1036,1034] else=[] elif=[] cc=[]
   leg @992  last=POP_JUMP_FORWARD_IF_TRUE ->1098   cond_succ=[1098, 996]
IfRegion entry=996  cond=996  merge=1040 then=[1008,1024,1036,1034,1098,1142,1200] else=[] elif=[] cc=[]
   leg @996  last=POP_JUMP_FORWARD_IF_TRUE ->1040   cond_succ=[1040, 1008]
IfRegion entry=1008 cond=1008 merge=1040 then=[1040] else=[1098] elif=[] cc=[1024]
   leg @1008 last=POP_JUMP_FORWARD_IF_FALSE ->1036  cond_succ=[1024, 1036]
   cc  @1024 last=POP_JUMP_FORWARD_IF_FALSE ->1098  cond_succ=[1098, 1034]
   jump @1034 last=JUMP_FORWARD ->1040 ; @1036 last=JUMP_FORWARD ->1098
```

Ownership check (same probe path): blocks 992/996/1008 belong to **no BoolOpRegion**
(`get_region_for_block` → `IfRegion@950`; the `cond_block in r.blocks` BoolOp scan is empty),
so the condition of IfRegion@992 is taken by the **`cond_instrs` route**.

Construction site that emits the wrong shape (sealed `region_ast_generator.py` = pristine
`gen_pristine.py`, identical line numbers to repo file `7d336164…`):
- `RegionASTGenerator._if_extract_condition_from_instructions` `:24016`;
- route `if cond_instrs:` `:24720`; polarity decision
  `negate = jumps_to_then2 != if_true2` `:24737` → for @992 the leg IF_TRUE→1098 (=merge, not a
  then entry) ⇒ `negate=True` ⇒ `if not include:`; same for @996 ⇒ `if not _query_date > pm_close:`;
- the adjacent `[BoolOp or pattern]` rescue `:24750–24771` cannot match @992 because it demands
  `len(region.then_blocks) == 1` (@992 has 6) and a single then block ending IF_FALSE;
- emitted at `return _negate_expr(expr) if negate else expr` `:24773`, arms consumed by
  `_if_generate_normal` `:21100` (then/else block dispatch) ⇒ three-level nest whose @994/@1006
  true exits slide to the tail **end** (idx254). That is the whole defect: no jump-target rewrite
  is needed, only the shape `and`-lift + `or`-tail merge + arm re-declaration.

`compile()` table (my mirror, my files; unit_diff + judge on each source):

| shape (source) | reading |
|---|---|
| nested (sealed product) | `delta=0 hunks=0 landings=2` judge 27/28 |
| C: `if not include:` + `if A or B: arm else: tail` (or-merge only) | `delta=0 hunks=0 landings=1` (`@994 →idx219 vs →idx254`) |
| B: `if not include and (A or B): arm` + tail as sibling (no else) | `len prod=1880 delta=−1`, hunk `- @1096 JUMP_FORWARD`, `hunks=1` |
| **A: `if not include and (A or B): arm else: tail`** | `delta=0 hunks=0 landings=0 judge_diff=False`; file judge **28/28** |

## 4. Criterion as implemented

New method `_r4701_and_lift_or_tail(self, region, cond_block, expr)` at patched `:19113`
(whole block inserted before `_if_generate_elif_chain`), called from the `cond_instrs` route at
patched `:24914–24923`, immediately after the existing `[BoolOp or pattern]` block and before
`return _negate_expr(expr) ...`, guarded by `if negate and not region.else_blocks:` (mutually
exclusive with the or-pattern route, which clears `negate` when it fires).

Predicate (pure CFG structural facts — no names, no offsets, no jump operands, no file whitelist;
same family as `_r2119` but for a **single-leg region with no BoolOpRegion**):
① `region.cond_block` ends `IF_TRUE` (not NONE_CHECK) on `T`, `T is region.merge_block`,
`region.else_blocks` empty; its only non-`T` conditional successor is `F` with `F < T`;
② `F` is the entry of an `IfRegion FR` with `FR.condition_block is F`, `FR.else_blocks` empty, no
`elif_conditions`, FR's leg ends `IF_TRUE → T2` with `T2 is FR.merge_block`, `T2 < T`;
③ FR leg's only non-`T2` conditional successor `FF` (`FF < T2`) is the entry of an `IfRegion FFR`
with `FFR.merge_block is T2`, no `elif_conditions`; FFR's condition rebuilds (chained compare via
`_build_chained_compare_from_region_data`, else `expr_reconstructor`), and A rebuilds from F's
pure instructions;
④ FFR's exit-block `IF_FALSE` target `E` satisfies **`E is T`** — the inner if's else arm is
exactly the block the outer leg jumps to — and `E > T2`, `E not in FFR.then_blocks`.

Action (this is why it is a shape/declaration change, per falsified axis (a)): test =
`BoolOp('and', [not X, BoolOp('or', [A, B])])`; arms re-declared `region.then_blocks=[T2]`,
`region.else_blocks=[E]`, `region.merge_block=None`; interior blocks `F`, `FF`, FFR's cc blocks and
every FR/FFR content block in `[F, T)` except `T2`/`E` are marked generated. Any failed conjunct
returns `None` and the old negate path runs byte-unchanged. For api_base: R=@992(X=`include`),
FR=@996(A=`_query_date > pm_close_market_datetime`), FFR=@1008(B=chained compare), T=1098,
T2=1040, E=1098 ⇒ emits exactly shape A. No analyzer edit; ownership untouched (§7).

## 5. Post-patch victim + fire census + quotation + panel

Victim (patched mirror `75582897726d72b8`, fresh product `scratch/out/api_base_r47.py`):
```
$ unit_diff.py api_base.pyc get_history_df --prod scratch/out/api_base_r47.py --all
len orig=1881 prod=1881 delta=0
hunks=0 landings=0 judge_diff=False
$ pyc_verify single api_base.pyc --source scratch/out/api_base_r47.py
[single] status=success units=28/28 success_rate=100.00%
```
Freshness/repro: delete-then-regen; my product and the panel-rig's independently regenerated
product are byte-identical (`cmp FRESH_REPRO_IDENTICAL`, sha16 `ec75d27dd3135041`).

Emitted source (both are the whole diff vs the sealed product, 1 hunk):
```python
            if not include and (_query_date > pm_close_market_datetime or am_close_market_datetime < _query_date <= pm_open_market_datetime):
                real_data = engine_obj.real_quote_handler.get_real_minute_kline(symbol, True)
            else:
                _last_real_58 = now_date * 10000 + 1458
                ...
```

**Fire census** (`D:/Temp/r47/scratch/sweep_r47.py`, class-level wrappers on
`_r4701_and_lift_or_tail` AND `_r2119_or_tail_extension` — one wrapper covers every generator
instance; log = `D:/Temp/r47/logs/sweep_r47.log`; roster 405 pyc↔product files, 7 batches,
all 405 generated, **0 ERR**):
- **TOTAL_FIRES(r4701) = 1**, in exactly one file: `IQData/api/api_base.pyc`,
  `entries=[('r4701', 992, 992)]` — region @992 verified dispatched (call log
  `calls=[992, 2686]`: 2 predicate attempts in this unit, 1 accepted, IfRegion@2686 correctly
  rejected).
- TOTAL_FIRES(r2119) = 2 (`strategy.pyc (512,512),(982,982)`) — the landed criterion's own census
  is unchanged, i.e. no pair-interaction suppression (strategy product byte-SAME below).
- 404 of 405 files: 0 fires ⇒ no state mutation ⇒ provably inert, corroborated byte-wise by the
  panel (13/14 products byte-identical to the repo's committed products via `cmp`).

Panel (`python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r47/wt r47a 0 14`,
log `D:/Temp/t30/log_panel_r47a.txt`; CHANGED/SAME is raw-byte `cmp` against the repo product):

| file | sealed count | patched | product vs repo |
|---|---|---|---|
| `fly/data/quotation.pyc` | 153/153 | **153/153** ✅ | SAME |
| `fly/data/quote.pyc` | 91/92 | **91/92** ✅ | SAME |
| `IQCommon/api/klinedata.pyc` | 64/64 | **64/64** ✅ | SAME |
| `IQCommon/logger/handlers.pyc` | 29/30 | **29/30** ✅ | SAME |
| `IQCommon/strategy/wizard_quant_api.pyc` | 58/58 | **58/58** ✅ | SAME |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | **38/41** ✅ | SAME |
| `IQData/api/api_base.pyc` | 27/28 | **28/28** ✅ FLIP | **CHANGED** (33 123 B) |
| `IQData/plugins/.../real_quote.pyc` | 45/45 | **45/45** ✅ | SAME |
| `IQEngine/.../strategy/strategy.pyc` | 27/27 | **27/27** ✅ | SAME |
| `IQEngine/.../fly_api/order_api.pyc` | 37/37 | **37/37** ✅ | SAME |
| `IQEngine/.../trade/trade_live_broker.pyc` | 121/128 | **121/128** ✅ | SAME |
| `IQEngine/.../matcher/matcher.pyc` | 17/17 | **17/17** ✅ | SAME |
| `IQEngine/.../realtime_event_source.pyc` | 12/13 | **12/13** ✅ | SAME |
| `IQEngine/.../risk_calculation/__init__.pyc` | 43/43 | **43/43** ✅ | SAME |

No count decreased; exactly one file flipped; quotation (the cheapest unit-level witness,
153/153) holds byte-exactly.

## 6. Negative evidence (measured numbers)

* or-merge only, outer nest kept (shape C) — measured on my mirror: `delta=0 hunks=0 landings=1`
  (`orig[193] @994 →idx219 | prod →idx254`). Confirms the `and`-lift of @992 is required on top
  of the tail merge; a criterion implementing only the single-leg version of `_r2119` would stop
  here.
* tail as following sibling (shape B, i.e. merge the test but do **not** re-declare `else=[E]`):
  `len prod=1880 delta=−1`, `delete orig[218..219] @1096 JUMP_FORWARD`, `hunks=1`. The arm
  re-declaration is mandatory, matching the predecessor's finding for the or-fold family.
* conjunct ④ `E is T` is what makes this an *adopted else*, not a generic merge: without reading
  FFR's IF_FALSE exit as the outer leg target, the shape reduces to C (1 landing). Removal was
  not needed to demonstrate this — C's measurement is exactly the predicate-minus-④ shape.
* predicate attempts vs fires in the victim file itself: 2 calls, 1 fire — IfRegion@2686 reaches
  the guard (`negate and not else_blocks`) and is rejected, so the criterion is not "fires on
  every negated single-leg if".
* corpus containment: fires = 1 file / 1 site out of 405 generated files (0 ERR); all 13
  non-victim panel products byte-SAME ⇒ zero collateral mutation.
* falsified axes honored, not re-run: no "land the tail jump on the declared merge" criterion
  (no jump operands in AST), no `_identify_conditional_regions` stop-set/ownership edit
  (zero edits outside `region_ast_generator.py`).

## 7. Declaration

**CANDIDATE READY (file flip: api_base 28/28)**

* Owner file: `core/cfg/region_ast_generator.py`. Candidate =
  `D:/Temp/r47/DELIVER/CANDIDATE_region_ast_generator.py` (whole file, 3 788 111 bytes,
  `sha256 | cut -c1-16` = **`75582897726d72b8`**), +150 CRLF lines / −0 vs sealed `7d336164eff5bf65`,
  pure CRLF preserved (`\r` count == `\r\n` count, zero `\r\r\n`), `py_compile` clean.
* Measured gate delta: `+1 unit / +1 file` expected (6603→6604 units, 396→397 files), corpus-wide
  fire footprint = one region in the victim file.
* No analyzer ticket required: ownership/identification were not touched; the fix is entirely a
  generator-side shape/declaration change (`_r4701_and_lift_or_tail`).
