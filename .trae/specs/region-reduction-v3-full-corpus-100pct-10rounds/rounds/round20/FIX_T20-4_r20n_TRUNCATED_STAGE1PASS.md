# FIX_T20-4 — r20n — region_analyzer declared short-circuit chain (BoolOp) ownership

STATUS: IN PROGRESS (appending as work proceeds)

## 0. Task as received (pre-digested, not re-derived)
- Single mechanism owned: `core/cfg/region_analyzer.py` — change what the analyzer
  **declares at identification time** about short-circuit (BoolOp) condition chains so
  the generator gets a chain it can fold.
- Measured upstream (given, do not re-derive): at cond blocks **512** (strategy) and
  **992** (api_base), `region.inline_boolop_chains[id(cond_block)]` is `None` /
  `ibc_blocks=[]`. Generator fold at `region_ast_generator.py:20989`
  (`_main_ibc = ...reconstruct(...)`) and fallback at `:21141`
  (`if _d_cb is cond_block:`) therefore never see a chain.
- Two ownership facts (given): (a) strategy — elif's third operand block **536** is owned by
  `IfRegion entry=536`, so flat `elif A or B or C` cannot fold at `IfRegion entry=512`
  (declared `merge=568`, `cond=524`, `then=[536,552,564,562,612,...]`);
  (b) api_base — `else=[1098]` assigned to `IfRegion entry=1008` (`merge=1040`) instead of
  `IfRegion entry=992` (`merge=1098 else=[]`).
- Ordering constraint (given, read, respected): `_identify_conditional_regions` walks
  `get_blocks_in_order()` ascending => parents identified before children. Wall write-up:
  `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round20/NOTE_T20_ORDERING_WALL.md`.
- OFF-LIMITS (already falsified): `core/cfg/region_ast_generator.py`,
  `core/cfg/ast_generator_v2.py` are READ-ONLY for me; generator axis closed
  (no channel writing a declared merge into an emitted jump target).
  Adjudication: `rounds/round20/ADJUDICATION_R20_MERGE_LANDING_FALSIFIED.md` §1 §2 §4.
- Bar: ONE named file flip — `strategy_universe` 27/27 OR `api_base` 28/28 — with the other
  file and all sentinels NOT decreasing and all six batteries at recorded values.
  Landings-only (4->2 with no unit flip) = FALSIFIED-with-evidence, said plainly.
- No git writes; source repo read-only; all products to `D:/Temp/r20n/out`.

## 1. Mirror build proof
Built per protocol at `D:/Temp/r20n/wt`, battery dirs copied with `cp --parents -r` at the
identical relative depth (runners resolve ROOT by 7 dirname levels).

Sealed-hash self-certification (`sha256sum | cut -c1-16`), repo vs mirror:

```
REPO dff6e81a5f2ff9f6  core/cfg/region_ast_generator.py     MIRR dff6e81a5f2ff9f6
REPO beeaf14435e22922  core/cfg/ast_generator_v2.py         MIRR beeaf14435e22922
REPO 640d33a77dcb71c2  core/cfg/region_analyzer.py          MIRR 640d33a77dcb71c2
```

All three match the sealed values in the brief. Full-tree byte sweep:
`for f in $(find core parsers utils bytecode scripts -name '*.py'); do cmp -s $f mirror/$f; done`
→ **zero DIFF lines**, so the mirror executes the landed bytes.
Measurement rig `unit_diff.py` was copied to the mirror at the same depth
(`SPEC_DIR/../../..` therefore resolves to the mirror root — verified by reading `:18`).

Corpus-product proof (mirror regenerates a committed product identically): see §2b below
(`fly/data/quotation.pyc` 153/153 from the mirror plus the `cmp` against the repo product).

Inputs: `.pyc` read from the REPO (`site-packages/...` absolute paths).
Products: written only to `D:/Temp/r20n/out/<tag>/`. No `*OK.py` was written into the repo.
No `git` write was performed at any point.

### 1b. Target-path correction (measured, not assumed)
The ticket's pyc paths do not exist / do not hold the named units. The files whose code-object
totals match the sealed baseline numbers are:

| ticket name | ticket path (wrong) | real path (matched by unit total + unit name) |
|---|---|---|
| strategy_universe | `IQEngine/core/strategy/strategy_universe.pyc` (11 code objs, no `tick_worker_thread`) | `site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` (27 code objs, has `tick_worker_thread`) |
| api_base | `IQEngine/plugins/plugin_system_api/api_base.pyc` (absent) | `site-packages/IQData/api/api_base.pyc` (28 code objs, has `get_history_df`). `IQEngine/api/api_base.pyc` exists but has no `get_history_df` |
| trade_live_broker | `IQEngine/plugins/plugin_system_broker/...` (absent) | `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` (128 code objs) |
| real_quote | `IQEngine/datafeed/...` (absent) | `site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc` (45 code objs) |
| matcher | `IQEngine/core/matcher.pyc` (absent) | `site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc` (17) |
| order_api | `IQEngine/core/order_api.pyc` (absent) | `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` (37) |

Harness used for every reading below: `python -X utf8 D:/Temp/r20n/tools/stage.py <tag>`
(which shells `pycdc.py --region <abs pyc> -o out/<tag>/<flat>OK.py` **from the mirror**, then
`scripts/pyc_verify.py single <abs pyc> --source <that product>` and
`unit_diff.py <abs pyc> <qualname> --prod <that product>`).

## 2. Stage 1 baseline table
口径 = `python -X utf8 D:/Temp/r20n/tools/stage.py pristine` run in `D:/Temp/r20n/wt`
(unpatched mirror), wall clock 175 s. **Every value reproduces the sealed baseline.**

| file | units (pyc_verify single) | named unit (unit_diff) | len orig/prod | delta | hunks | landings |
|---|---|---|---|---|---|---|
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | **26/27** | `<module>.Strategy.tick_worker_thread` | 288/288 | 0 | 0 | **4** |
| `IQData/api/api_base.pyc` | **27/28** | `<module>.get_history_df` | 1881/1881 | 0 | 0 | **2** |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | **118/128** | 3 pure-landing units (bare names, see §3) | — | — | — | 1 each |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | **43/45** | `<module>.RealQuoteData.get_tick_direction` | 295/296 | +1 | 1 | 1 |
| `fly/data/quotation.pyc` (sentinel) | **153/153** status=success | — | — | — | — | — |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` (sentinel) | **17/17** status=success | — | — | — | — | — |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` (sentinel) | **37/37** status=success | — | — | — | — | — |

### 2b. Corpus-product equality proof (protocol step 2, final clause)
Mirror-regenerated products `cmp`-ed byte-for-byte against the repo's committed products:

```
IDENTICAL site-packages/fly/data/quotationOK.py                       (182759 B)
IDENTICAL site-packages/IQData/api/api_baseOK.py                       (33228 B)
IDENTICAL site-packages/IQEngine/plugins/plugin_system_matcher/matcherOK.py (13299 B)
```

⇒ every later mirror reading in this doc is trustworthy: the mirror's decompiler is a
byte-exact producer of the landed corpus output.

### 2c. Six batteries, unpatched mirror (口径 = each dir's own committed runner, cwd = mirror root)
| battery | command | reading | recorded base | match |
|---|---|---|---|---|
| repro | `rounds/round14/repro/run_repro.py` | `RED=9 / 9` | 9R/9 | ✓ |
| arm | `rounds/round14/repro_arm/run_arm.py` | `GREEN=0 RED=3 / 3` | 0G/3R | ✓ |
| ccneg | `rounds/round14/repro_ccneg/run_ccneg.py` | `GREEN=3 RED=1 / 4` | 3G/1R | ✓ |
| retbreak | `rounds/round18/repro_retbreak/run_retbreak.py` | `GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4` | 2G/2R DRIFT=0 | ✓ |
| orderapi | `rounds/round19/repro_orderapi/run_orderapi.py` | `GREEN=5 RED=0 / 5` | 5G/0R | ✓ |
| tail | `rounds/round19/repro_tail/make_tail.py --run` | `GREEN=13 RED=0 / 13` | 13G/0R | ✓ |

**STAGE 1 = PASS.** Each runner self-prints `ROOT=D:\Temp\r20n\wt`, confirming the mirror
depth is right and no battery measured the live tree.

(TODO: batteries + corpus-product cmp proof)

## 3. Per-unit 取证
(TODO)

## 4. 判据实现 (criterion implemented)
(TODO — must not be left blank)

## 5. Stage readings
(TODO)

## 6. 负面证据 (negative evidence)
(TODO)

## 7. Final declaration
(TODO)
