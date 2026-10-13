# R21-66 — `trade_live_broker._sync_worker` SECOND loop: chained-compare latch absorbed into the loop re-test

Engineer r95a. Mirror: `D:/Temp/r95`. Repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` **untouched**.
Slice: **ninth addendum item 4 only** (`TICKET_R21-59…md`, `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round40/`).
Orthogonal to r93a (analyzer condition assembly) and r94a (generator chain consumption, analyzer candidate `241905c2078f0270`); built on the **plain landed bytes** only. The while-condition chain-**mounting** code paths are NOT touched.

## 0. Base / provenance (re-measured here, not inherited)

Mirror built by copying repo `core parsers bytecode utils scripts pycdc.py` into `D:/Temp/r95`:

| file | bytes | sha16 | expected |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 3852304 | `b4363f5858e58074` | MATCH |
| `core/cfg/region_analyzer.py` | 2109362 | `842e2748bcdfeb66` | MATCH |

Base re-measure (`python -X utf8 pycdc.py …/trade_live_broker.pyc -o out/broker_BASE.py`):

- product `out/broker_BASE.py` 179288 B, **`cmp`-identical** to `D:/Temp/r91m/out/broker_LANDED.py` (the landed reference).
- judge `python -X utf8 scripts/pyc_verify.py single <pyc> --source out/broker_BASE.py` →
  `status=failure units=127/128 success_rate=99.22%`, sole failing unit
  `***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow`. **127/128 reproduced.**
- rig `win_r91.py <pyc> _sync_worker out/broker_BASE.py` (r91a's rig; **aligns on opcode names only**, so its window
  counts are NOT interchangeable with `allwin`'s — both are reported where used):
  `orig instrs=412 prod instrs=410 delta=-2`, **windows=9** (`logs/win_BASE.txt`) — identical to the r91a baseline table.

## 1. Item 4 quoted, and the mechanism RE-VERIFIED on the bytes

Brief's item-4 pair. Landed product `out/broker_BASE.py` lines 855/863-866 vs
GOLD `r91/broker_GOLD_PROOF.py` (128/128) / `r91/true_source_sync_worker.py` lines 33-43:

```python
# LANDED (wrong, two symptoms of ONE region LoopRegion@1890)
                sync_data_flag = 1                      # L855  printed UNCONDITIONALLY
                time.sleep(steps)                       # L863
                if not pre_before_trading <= int(…strftime('%H%M')) < int(post_after_trading):
                    continue                            # L864-865 loop-tail chain as if-not-guard
                time_difference = abs((… - self.sync_account_time).total_seconds())   # L866
# GOLD (right)
                time_difference = abs((… - self.sync_account_time).total_seconds())
                if time_difference > sync_max_time:
                    sync_data_flag = 1
                …
                time.sleep(steps)                       # chain lives in the loop's own re-test, not in the body
```

Read-only CFG/analyzer dump (`dump_r95.py`, `logs/dump_l3*.txt`; nothing mutated inside the analyzer):
unit `_sync_worker` = 54 blocks; the second loop is

```
LoopRegion@1890 hdr=2072 cond=1890 be=2844 bes=[2844] cc=[2026]
   meta={'chained_compare_ops': ['<=', '<'], 'is_chained_compare_cond': True}
   body=[2072,2090,2114,2136,2168,2192,2198,2200,2206,2208,2214,2374,2378,2382,
         2492,2540,2580,2628,2668,2844,2884]
```

Blocks that matter (opcode-level facts, verbatim from the dump):

| block | n | content | terminator |
|---|---|---|---|
| @1890 (cond) | 17 | `pre_before_trading` … `int(int(strftime))` `SWAP 2` `COPY 2` `COMPARE_OP <=` | `POP_JUMP_FORWARD_IF_FALSE 2066` |
| @2026 (chain[0]) | 7 | `int(post_after_trading)` `COMPARE_OP <` | `POP_JUMP_FORWARD_IF_FALSE 2886` |
| **@2214** | 19 | `time_difference = abs(…)` **STORE_FAST** + `time_difference > sync_max_time` | `POP_JUMP_FORWARD_IF_FALSE 2378` |
| @2374 | 2 | `LOAD_CONST 1` `STORE_FAST sync_data_flag` (the *then* of @2214's real `if`) | falls to 2378 |
| **@2668** | 23 | `time.sleep(steps)` … **POP_TOP** (expression statement) then a byte-for-byte copy of @1890's evaluation (`… SWAP 2 COPY 2 COMPARE_OP <=`) | `POP_JUMP_FORWARD_IF_FALSE 2884` |
| **@2844** (be) | 7 | a copy of @2026's evaluation (`LOAD_GLOBAL int / LOAD_FAST post / PRECALL / CALL / COMPARE_OP <` / `EXTENDED_ARG`) | `POP_JUMP_BACKWARD_IF_TRUE 2072` (back to the body start) |
| @2884 | 1 | `POP_TOP` | falls to 2886 |

So CPython emitted the loop test `pre <= int(…) < int(post)` twice (entry @1890+@2026, latch @2668-tail+@2844)
exactly per the briefed layout law, and the latch's second leg is a conditional **backward** edge onto the body
start (@2844→@2072).

**r91a's mechanism sentence — re-verified, and refined.** All three of item 4's symptoms live in ONE code path:
`_loop_generate_while`'s chained-compare suppression loop, `region_ast_generator.py:8126-8174`, which is gated on
`region.metadata['is_chained_compare_cond']` (so its reach is the population I census in §2). Inside it:

1. `:8135-8151` — the store extractor fires when the body block has a `STORE_*` and the *post-store* ops merely
   `any(COPY|COMPARE_OP|IS_OP|CONTAINS_OP)` (`:8141`). `@2214` **is** such a block (`STORE_FAST time_difference`
   followed by `COMPARE_OP >`), so it is mis-read as "loop increment + condition recheck": the block is suppressed
   whole, its store is re-appended **at the end of the body** (`recheck_store_stmts` → `:8229 body_stmts.extend`)
   and `@2214`'s genuine `if` (IfRegion@2214, then=@2374) never renders → `sync_data_flag = 1` prints unconditionally
   at L855 and `time_difference = …` prints at L866. **This is symptom (B) and it is NOT in r91a's sentence: it is
   an over-fire of the existing extractor, not a failure of it.**
2. `@2668` contains **no `STORE_*`** at all — its prefix is the POP_TOP-terminated expression statement
   `time.sleep(steps)`. `_last_store_idx` stays `-1` (`:8136-8139`), so the extractor never fires and the block is
   emitted as statements: `time.sleep(steps)` + IfRegion@2668 (`is_empty_then_chained_compare=True`) →
   `if not <chain>: continue`. **Confirms r91a's "prefix is a POP_TOP expression statement so the store-extractor
   never fires".** = symptom (A).
3. `:8153-8159` — the pure-recheck suppression applies only to `_b is region.back_edge_block` **and** requires
   every non-jump op to be in the whitelist `LOAD_*/COPY/SWAP/COMPARE_OP/IS_OP/CONTAINS_OP/POP_TOP`. `@2844` is the
   back_edge block but carries `PRECALL`/`CALL` (the `int(post_after_trading)` operand), so `_has_only_compare` is
   False and the block survives. **Confirms r91a's "_has_only_compare rejects CALL-bearing operands".** = symptom (C).

(Not item 4: `COMPARE_OP` parity is 21/21 as briefed, so nothing is missing at the instruction-count level; my
change moves/removes no compare, it re-homes the latch copy.)

## 2. Census (real bytes, read-only rig `census_r95.py`; nothing mutated inside the analyzer)

Predicate vocabulary (all block-local opcode class / stack-shape / region data / pred-succ facts):
for a `LoopRegion` L that the generator can even reach — gate at `region_ast_generator.py:8102-8108`,
`is_chained_compare_cond` ∧ `condition_chain_blocks` non-empty ∧ `len(chained_compare_ops) >= 2` —
let **SEG** = {opcode-name sequence of `condition_block` minus NOISE minus its conditional terminator}
∪ {same for each `condition_chain_block`}. For each body block `b` (not header/cond/chain/back-edge)
ending in a conditional jump, split at the last *statement boundary* (`STORE_*` / `POP_TOP`) into
prefix and tail **T**:

* **hitA** = `T == some s ∈ SEG` and the boundary is `POP_TOP` — item-4 symptom (A)/(C) carrier;
* **hitB** = the landed `_is_recheck` (`:8141`, "post-store merely contains a compare op") fires but
  `T != every s ∈ SEG` — over-fire, symptom (B) carrier;
* **hitC** = `L.back_edge_block`'s whole non-jump sequence `== some s ∈ SEG` yet it is outside the
  `_has_only_compare` whitelist — symptom (C) carrier.

`census_r95.py <budget> <pathlist>` walks **every code object** of each product, runs the landed
analyzer only (`build_cfg` + `RegionAnalyzer.analyze`), and **never imports or runs the generator**,
so it cannot alter a product. Non-reachability of the same tests for loops without the gate is
reported as `noncc`.

### 2.1 Panel (22 files = the 20-file pre-gate panel + `replace_utils` + `risk_calculation/function`)

`logs/census_panel22.txt`, 37 s:

| file | cc-loops (reachable) | A | B | C | noncc B | noncc C |
|---|---|---|---|---|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | **1** | **1** | **1** | **1** | 19 | 7 |
| every other panel file (21 rows: quotation, quote, klinedata, handlers, wizard_quant_api, trade_info_utils, api_base, real_quote, strategy, order_api, matcher, realtime_event_source, risk_calculation/`__init__`, arg_checker ×3, profiler_func ×3, replace_utils, function) | 0 | 0 | 0 | 0 | 31 total | 14 total |
| **panel total** | **1** | **1** | **1** | **1** | **31** | **14** |

### 2.2 Whole corpus (all 402 products, `logs/census_corpus.txt`, 80 s, 0 MISSING / 0 ANALYZE_FAIL)

```
DONE files=402 cc_loops=1 other_loops=172 A=1 B=1 C=1 noncc_A=0 noncc_B=87 noncc_C=48 elapsed=80s
FILE …/trade_live_broker.pyc cc_loops=1 other_loops=17 A=1 B=1 C=1 | noncc A=0 B=19 C=7
  CC unit=_sync_worker loop@1890 cond=@1890 seglens=[6, 16] A=[2668] B=[2214] C=[2844]
```

**The rule touches exactly ONE loop region in the entire corpus**, and all three hits are the three
blocks of item 4 (`@2668` A, `@2214` B, `@2844` C). Cross-check on the population size: loop
conditions with a non-None `condition_block` = 172 + 1 = **173 corpus-wide** and 81 + 1 = **82 in the
panel** — identical to r90a's independently written census of the same population
(`round40/ADJUDICATION_ROUND40.md` l.118: "82 loop conditions in the 20-file panel and 173 across all
402 files"), so the rig's walk is complete, not silently truncated. `noncc_B=87 / noncc_C=48` shows
the *same tests* would fire on many ungated loops — my conjuncts live inside the `is_chained_compare_cond`
branch and cannot reach them (measured in §5: the 402-product sweep is the proof).

### 2.3 Probe inertness

`census_r95.py` / `dump_r95.py` are standalone processes; they import `core.cfg` read-only and never
touch `region_ast_generator.py`. Proven anyway: after both runs, the mirror files still hash
`b4363f5858e58074` / `842e2748bcdfeb66` and `out/broker_BASE.py` re-generates `cmp`-identical (§4).


## 3. Implementation (generator half only; analyzer untouched, stays `842e2748bcdfeb66`)

Candidate `core/cfg/region_ast_generator.py` = landed bytes + 3 hunks inside the ONE code path the
census proved reachable (`_loop_generate_while`, chained-compare suppression loop):
**sha16 `0f4c3898298e6f2e`**, 3860104 bytes, UTF-8 BOM, all-CRLF, CR-CR-LF count 0, no bare LF,
`py_compile` passes. Builder `build_r95.py` regenerates it byte-exactly from
`seed/region_ast_generator_LANDED_b4363f5858e58074.py` (byte-identical copy of the repo's landed file).

| hunk | candidate lines | what it does |
|---|---|---|
| H1 | `:8118-8141` | builds `_r2166_seg_set` = the loop's own condition-segment opcode-name sequences (`condition_block` + `condition_chain_blocks`, NOISE + `EXTENDED_ARG` + conditional terminator dropped). |
| H2 | `:8157-8201` | statement-boundary set `STORE_*` union `POP_TOP`; `_r2166_is_latch_copy` = "tail after the last boundary == some segment of my own condition"; `_r2166_latch_end` = "back_edge_block or header_block is among this block's successors"; and **tightens** the landed store extractor to `if _is_recheck and _r2166_is_latch_copy and _r2166_bnd_idx == _last_store_idx:` — it no longer eats a plain `s = e(); if s > k:` statement. |
| H3 | `:8203-8251` | **case A** — expression-statement prefix + latch copy: rebuild the prefix through the existing `_build_store_statement` -> `_build_statement` pair, push it onto the existing `recheck_store_stmts` channel, mark the block generated, `continue`; if the rebuild fails nothing is suppressed (no silent statement loss). **case C** — `_has_only_compare or _r2166_pure_copy` for the `back_edge_block`. |

Constraints held: bottom-up, unique block membership (only `generated_blocks`/`generated_offsets`
adds, same idiom as the landed code beside it); nested regions stay abstract (no child region
touched); correct-at-identification (the decision is made once from block data before emission — no
retrospective repair of the emitted tree); one-way dataflow (append-only into `recheck_store_stmts`);
criteria are opcode class + stack-shape statement terminators + region data
(`condition_block`/`condition_chain_blocks`/`back_edge_block`/`header_block`/`body_blocks`) +
successor relations. **No function name, no file name, no absolute offset, no counter, no threshold,
no magic number.** The while-condition chain-**mounting** paths (r93a/r94a territory: analyzer
candidate `241905c2078f0270`, generator `boolop_for_while` consumption at `:7776-7810`) are untouched.

## 4. Half measurement — my generator alone on the landed analyzer

`_sync_worker` second loop: candidate text vs GOLD text (extracted `while pre_before_trading <= ... < ...:`
block, `diff`) = **IDENTICAL** (see the rig output quoted below).

Whole-unit effect (`win_r91.py`, opcode-name alignment; `allwin` counts are NOT interchangeable with
this rig's — both reported, mine used only for before/after of the same rig):

| product | instrs | windows | del | ins | vs GOLD (win/del/ins) | `SWAP` (chained-cmp copies) | backward-cond | `COMPARE_OP` |
|---|---|---|---|---|---|---|---|---|
| landed `broker_BASE.py` | 410 | 9 | 206 | 208 | 9 / 207 / 205 | **3** | 2 | 21 |
| candidate `broker_R66.py` | 387 | **6** | 136 | 161 | **6 / 136 / 157** | **2** | 2 | 20 |
| GOLD `broker_GOLD_PROOF.py` | 408 | 4 | 5 | 1 | — | 2 | 4 | 21 |

Before -> after, the exact lines the brief quotes (base L855/L863-866 -> candidate L854-856/L863):

```python
# BEFORE (landed)                                       # AFTER (candidate) = GOLD
                sync_data_flag = 1                       time_difference = abs((datetime.datetime.now()
                ...                                          - self.sync_account_time).total_seconds())
                time.sleep(steps)                        if time_difference > sync_max_time:
                if not pre_before_trading <= int(...) < int(post):    sync_data_flag = 1
                    continue                             ...
                time_difference = abs((...) - self.sync_account_time)...)  time.sleep(steps)
```

The second-loop block (`while pre_before_trading <= ... < int(post_after_trading):` through its last
body statement) is 19 lines in the landed product and 18 in GOLD; `difflib` on that extracted block:
landed vs GOLD = 3 changed lines + 3 deleted lines (item 4); **candidate vs GOLD = IDENTICAL**.

**Which of the four GOLD differences this closes: item 4 only, and both of its halves** —
(i) the unconditional bare `sync_data_flag = 1` becomes the guarded store under
`if time_difference > sync_max_time:` (H2 tightening), and (ii) the loop-tail chained comparison
stops printing as `if not <chain>: continue` and is absorbed into the loop's own re-test (H3 case A +
case C). Items **1, 2 and 3 stay open** and are not touched by this patch (1+2 = chain mounting /
latch consumption = r93a+r94a; 3 = flat-vs-nested `and`-chain). Accordingly there is **no full flip by
myself**, as briefed: judge stays `127/128`, sole failing unit still `_sync_worker`.
Evidence the change is item-4-shaped and not noise: the third duplicated chained comparison disappears
(`SWAP` 3 -> 2), i.e. the chain is now evaluated exactly twice as in the original and in GOLD; windows
9 -> 6; distance to GOLD 207/205 -> 136/157; the 6 remaining windows are all in the FIRST loop and the
`and`-chain (items 1-3), none in the second loop.

## 5. No-regression panel (`python -X utf8 scripts/pyc_verify.py single <pyc> --source <fresh product>`)

| file | required | candidate | note |
|---|---|---|---|
| `trade_live_broker.pyc` | 127/128 base | **127/128** | `_sync_worker` still `Different control flow` (items 1-3); the other 127 units Equal |
| `realtime_event_source.pyc` | 12/13 | **12/13** | `clock_worker` unchanged (not my slice) |
| `IQCommon/util/replace_utils.pyc` | 9/9 | **9/9** | success |
| `plugin_system_risk_calculation/function.pyc` | 15/15 | **15/15** | success |
| `fly/data/quote.pyc` | 92/92 | **92/92** | success |
| `fly/data/quotation.pyc` | 153/153 | **153/153** | success |
| `fly_api/order_api.pyc` | 37/37 | **37/37** | success |
| `arg_checker` x3 (IQCommon / IQData / IQEngine) | 49/49, 39/39, 43/43 | **49/49, 39/39, 43/43** | success |
| `profiler_func` x3 | 17/17, 15/15, 18/18 | **17/17, 15/15, 18/18** | success |

Canary reach: the duplicated modules contain **0** chained-compare loop regions (census 2.1), so my
predicate cannot reach them — they are collateral detectors here, and they are clean.
Log: `logs/panel_r95.txt`.

## 6. Mandatory 402-product sweep vs HEAD

Reference validity checked first: `git cat-file -p HEAD:site-packages/.../trade_live_brokerOK.py`
= 176226 B = CR-stripped `broker_BASE.py` exactly, so HEAD's committed products are the landed bytes'
output. Reference tree = `git -C <repo> archive HEAD site-packages | tar -x` scoped to `site-packages`
(5.1 MB, 407 `*OK.py`); nothing compared against checked-out files. Every product regenerated by my
mirror into `sp_out/` (repo never written; each product deleted before producing) and compared
CR-stripped. `sweep_r95.py`, 3 budget-guarded chunks, `logs/sweep_c{1,2,3}.txt`:

```
DONE same=401 changed=1 newprod=0 nooutput=0        (402/402 files, 0 NOINPUT, 0 NOPROD, 0 TIMEOUT)
CHANGED site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc (176226 -> 176135 bytes)
```

`CHANGED` is **not** empty — the predicate fired, on exactly the one file the census predicted. The
swept product is byte-identical to the judged `out/broker_R66.py` (re-checked), and its whole-file diff
against the landed product is 2 hunks, both inside `_sync_worker`'s second loop, 0 elsewhere.

## 7. Verdict / limits / merge notes

- Measured: item 4 closes (both halves); second-loop text == GOLD text; 0 regressions on the panel and
  in the 402-product sweep (`CHANGED = 1` = the target).
- Not claimed: no unit flip. `_sync_worker` still needs items 1-3 (r93a/r94a) to reach GOLD's 128/128.
  The campaign is not complete; this is a candidate, not a landing.
- Merge shape: analyzer byte-for-byte unchanged, so this candidate composes with `241905c2078f0270` in
  either order. The only shared file is `region_ast_generator.py`; my 3 hunks live at `:8118-8251`
  (chained-compare suppression loop), the chain-mounting/consumption hunks at `:7776-7810` + analyzer —
  disjoint anchors, so a rebase of either direction is a clean 3-hunk replay.
- Falsified on the way (so nobody re-spends a dispatch): `@2214` is not a *missing* latch case, it is an
  **over-fire** of the landed extractor (`_is_recheck` = "post-store merely contains a compare op").
  Tightening it is half of item 4 and is absent from r91a's mechanism sentence, which named only the
  two failure modes (`_has_only_compare` whitelist, POP_TOP prefix) — both of which I reproduced on the
  bytes (section 1).
- Ordering caveat, stated plainly: case A reuses the landed `recheck_store_stmts` channel, which appends
  the extracted statement after the body statements. That is correct here because the latch block is the
  body's last statement block (CPython layout law), and the census shows exactly one such block in the
  corpus; if a future corpus file produces a mid-body latch-fused block, this channel must be replaced by
  in-place emission before that rule is reused.

## 8. Delivered files (`D:/Temp/r95/DELIVER`), sha16 = sha256[:16] at rest

| file | bytes | sha16 |
|---|---|---|
| `DELIVER/region_ast_generator_R21-66_0f4c3898298e6f2e.py` | 3860104 | `0f4c3898298e6f2e` |
| `DELIVER/region_ast_generator_LANDED_b4363f5858e58074.py` | 3852304 | `b4363f5858e58074` |
| `DELIVER/build_r95.py` | 14434 | `9ccb7c41c7ef403b` |
| `DELIVER/census_r95.py` | 8593 | `2eb4f0499d28dd26` |
| `DELIVER/dump_r95.py` | 2592 | `558549889b1616fc` |
| `DELIVER/panel_r95.py` | 2053 | `9bb3dd3d23fe98bf` |
| `DELIVER/sweep_r95.py` | 2569 | `80ecdb1961fe6dbb` |
| `DELIVER/win_r91.py` | 2049 | `f49e13edc8937792` |
| `DELIVER/products/broker_BASE.py` | 179288 | `f25d834a6b0d763e` |
| `DELIVER/products/broker_R66.py` | 179196 | `e546c057f8c7189d` |
| `DELIVER/logs/census_corpus.txt` | 52956 | `959a72498c0cbd5d` |
| `DELIVER/logs/census_panel22.txt` | 4653 | `11d39875f9139840` |
| `DELIVER/logs/win_BASE.txt` | 22374 | `c74967f0027d8f59` |
| `DELIVER/logs/win_R66.txt` | 16125 | `d7b683b935d383f8` |
| `DELIVER/logs/panel_r95.txt` | 1464 | `2b103e7eedfa8a0f` |
| `DELIVER/logs/sweep_c1.txt` | 68 | `0ea91e18f67e25ba` |
| `DELIVER/logs/sweep_c2.txt` | 70 | `33ae8cd2c8de941d` |
| `DELIVER/logs/sweep_c3.txt` | 176 | `ca43a5b1cc5892c3` |

`build_r95.py` reads the repo landed file (`core/cfg/region_ast_generator.py`, asserts sha16
`b4363f5858e58074`), asserts the banked `seed/` copy is byte-identical to it, splices the 3 hunks by
CRLF-line anchors (each asserted unique), and writes the mirror file: re-running it reproduces
`0f4c3898298e6f2e` (verified twice this session). Nothing was installed into the repo;
`git -C <repo> status --porcelain -- core/` is empty and `... -- site-packages/ | grep OK.py`
reads 0 lines (measured after the sweep; §7/§9).

Rigs take absolute paths; `panel_r95.py` / `sweep_r95.py` hard-code `ROOT = D:/Temp/r95` and read the
corpus `.pyc` inputs from the repo, writing only under `D:/Temp/r95`.

## 9. Candidate text vs the GOLD oracle (the acceptance metric the round now uses)

`difflib` over the whole emitted `_sync_worker` function text, candidate vs `r91/broker_GOLD_PROOF.py`:
**3 hunks remain, 0 of them in the second loop** —

| hunk | content | which GOLD-diff item | owner |
|---|---|---|---|
| 1 | loop 1 prints one leg (`while int(..) < pre_before_trading:`) where GOLD prints the 4-leg `or`/`and` chain | item 1 | r93a (analyzer mounting) |
| 2 | loop 1's latch copy still printed as body statements (`return int(..) >= int(post)` + two `continue`s + `if holiday_sync_account == '0':`) | item 2 | r93a/r94a |
| 3 | the reconnect block is a flat `and`-chain ending in `break` where GOLD nests 4 `if`s ending in `return` | item 3 | the and-chain family |

Before my change the same diff had **5** hunks (the two extra hunks were `sync_data_flag = 1` printed
unguarded, and `if not <chain>: continue` + the hoisted `time_difference = ...` pair at the loop tail).
Both are gone — that is item 4 closing, and it is the honest acceptance bar for this slice: **no flip by
myself** (judge still 127/128, verdict class still `Different control flow`), the named difference
disappears, nothing else moves (401/402 products byte-identical to HEAD).
