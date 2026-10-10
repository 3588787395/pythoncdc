# DIAG R21-4 — trade_live_broker.pyc (118/128): mechanism census of the 10 failing units

Engineer `r23d` · diagnosis-only · branch `rr-v3r01-f557fd` · repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
Mirror `D:/Temp/r23d/wt` · products `D:/Temp/r23d/out` · READ-ONLY on repo (no `core/` patch, no gate, no repo `*OK.py` write, no `git` write).
State at start: HEAD `25fa7e7d`, gate 23 sealed = 6592/6617 units, 391/402 files, 25 residual units / 11 files.
Deliverable = **per-unit classification with a named host per bucket. No predicate was installed; nothing in this doc is a landed change.**

## Summary (the answer, ≤500 words)

**The broker's 10 failing units contain SEVEN distinct mechanisms, not one.** No single predicate closes this file.

Mirror first: 97 core-tree files hash-identical repo↔mirror, and the mirror regenerates `trade_live_brokerOK.py`
byte-identically (`6a71fc95…`, 178161 B, `cmp` clean) and judges identically (`118/128`, same 10 unit names).
So every number below is from a certified producer on the current landed bytes.

**How the 10 split.** B1 covers the most units — **three** (`_process_order` −465, `_process_cancel_order` −293,
`_sync_worker`): the generator prints a `break`/`continue`/`return` **before** the remainder of its own suite, and
CPython ≥3.10 dead-code elimination deletes that remainder from the bytecode. The proof is a census, not a story:
those three are the only units where the product AST has dead suites after a terminator (1/2/2 vs 0 on the other
seven), and the missing text is physically present in the product source (`_process_order` lines 430–493). Host
`region_ast_generator.py:_generate_block_statements_body:52557` (role→`Break` at 53051). This is the axis to ticket first.

**The three pure-landing units are three different mechanisms** — that is the headline negative for "one landing
criterion covers the trio". `_process_tick_order` is a `WHILE_LOOP` whose `entry=114 ≠ header_block=130`, so its
condition is tested once and the printed `while cond:` re-targets the back edge; its code object has **zero** IfRegions
with `merge_block is None`, so a merge-declaration patch cannot reach it. `rzrq_credit_order` genuinely has the missing
declaration (`IF_ELIF_CHAIN entry=2136, merge=None` owns the jumping tail). `get_ipo_stocks` has the merge declared
**correctly** (`merge=1154` = the original's landing) yet the product lands elsewhere, because the printed source fused
`if not X: (if A: continue)(if B: continue)` into `if X or A: continue / elif B: continue` — generator-side, host
`_if_extract_cond_instructions:17225`. The same fusion explains two of `ipo_stocks_order`'s three landings (B3, 2 units).
Remaining: `etf_basket_order` = an 11-instruction `else` arm printed after its whole then-side (B5, net-zero, 1 landing);
`_trade_status_handle` = the leading statement of the loop-header block never printed **in the text at all** plus the
back edge re-materialised as a condition re-test (B6); `etf_purchase_redemption` = f-string literal prefix polluted with
pending-stack names (B7) — and it is the only unit the judge calls `Different bytecode` rather than `Different control
flow`, which alone separates it from the other nine.

**What would have to close for 128/128:** all seven buckets (3+1+2+1+1+1+1 = 10). No bucket flips a file here, because a
file needs every unit Equal; the broker costs 7 mechanisms for 1 file, whereas each of the six one-unit-away files costs 1.
So the broker is the largest pool but the worst rate — B1 alone is the only bucket worth a ticket on yield (3 units, 758
instructions of loss).

**Corrections booked:** the sealed table's "del 471/300/18", "32 target diffs", "35 target diffs" and the "#16 co-requisite
patch" premise are all wrong against today's bytes; and `unit_diff.py --all` is documented but never parsed, which hides
1-instruction hunks on two of these units (recovered with my own dump).

## 1. Mirror proof

Landed bytes re-read by me (sha256 first-16, repo side):

| file | measured | expected | = |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | `4f295dfc6ebd2caa` | `4f295dfc6ebd2caa` | ✓ |
| `core/cfg/region_analyzer.py` | `ec6bd48826c65df9` | `ec6bd48826c65df9` | ✓ |
| `core/cfg/comprehension_generator.py` | `7d8acab92ccc7782` | `7d8acab92ccc7782` | ✓ |
| `core/cfg/ast_generator_v2.py` | `beeaf14435e22922` | `beeaf14435e22922` | ✓ |

Build: `cp -r pycdc.py core parsers utils bytecode scripts` + `cp --parents -r` of the six battery dirs
(`rounds/round14/{repro,repro_arm,repro_ccneg}`, `rounds/round18/repro_retbreak`, `rounds/round19/{repro_orderapi,repro_tail}`,
all present in repo and copied to identical relative depth) + `unit_diff.py` at its own relative depth.
**Whole-tree certification: 97 `.py` files under `core/ parsers/ utils/ bytecode/ scripts/` compared sha256[:16] repo vs mirror → mismatch = 0.**

Producer certification: from `D:/Temp/r23d/wt`, `python -X utf8 pycdc.py -o D:/Temp/r23d/out/trade_live_brokerOK.py <repo>/…/trade_live_broker.pyc`
→ 6.1 s, 178161 bytes; `cmp` against the repo's in-place `trade_live_brokerOK.py` → **identical** (both `6a71fc95a5e6b388`).
Second proof under the judge (not just bytes): `scripts/pyc_verify.py single <repo pyc> --source D:/Temp/r23d/out/trade_live_brokerOK.py`
→ `status=failure units=118/128` and the 10 named failures are exactly the 10 units of this ticket. So the mirror is a byte-exact producer *and* a faithful judged producer.
(Today's broker bytes differ from the round-14-era `6a7151f0f5e03687` quoted in memory — 10 gates have landed since; same size, same 118/128.)
`.pyc` inputs read from the repo; every product written under `D:/Temp/r23d/out`. Mirror never modified (§7).

## 2. Per-unit table (sealed landed bytes, `unit_diff.py` on the in-place product; classes per the brief's rules)

| unit qualname | len/delta/hunks/landings/judge_diff | class | first differing instruction pair (offset+opname) | one-line source-shape guess |
|---|---|---|---|---|
| `<module>.TradeLiveBroker._process_order` | 507/42 **−465** / 4 / 1 / True | content-loss (del 468, ins 3) | orig`@98 LOAD_FAST self` ‖ prod`@92 LOAD_FAST self`; mass hunk orig`@470 LOAD_CONST 2` ‖ prod`@194 RETURN_VALUE` | `break` emitted at product line 429 **before** the rest of the `while` suite (lines 430–493) → CPython 3.10+ dead-code elimination deletes it; also the try/finally pop block printed at the suite end |
| `…_process_tick_order` | 182/182 0 / 0 / 1 / True | **pure-landing** | `@178 JUMP_BACKWARD` orig→idx22 (`@130 LOAD_GLOBAL len`) ‖ prod→idx19 (`@114 LOAD_FAST self`) | analyzer declares `WHILE_LOOP entry=114 header_block=130` (condition tested once); generator prints `while self.before_trading_start:` so the back edge re-tests |
| `…_process_cancel_order` | 333/40 **−293** / 3 / 0 / True | content-loss (del 297, ins 4) | orig`@332 LOAD_FAST order` ‖ prod`@110 LOAD_CONST None` | `continue` at product line 528 (and 564) printed before the remaining body (lines 529–569) → DCE |
| `…_sync_worker` | 404/401 −3 / 5 / 6 / True | **mixed** (ins 214 / del 223) | orig`@362 POP_JUMP_FORWARD_IF_TRUE` ‖ prod`@362 POP_JUMP_FORWARD_IF_FALSE` | inverted pre-trading window leg + spurious `return` at line 855 (DCE of 856–860) + a 162-instr arm printed ~120 indices early (177-instr block lands at prod idx 114) |
| `…_trade_status_handle` | 127/124 −3 / 3 / 2 / True | content-loss (del 10, ins 7) | orig`@46 LOAD_GLOBAL get_trade_status` ‖ prod`@44 LOAD_FAST self` | the **leading statement** of the loop-header block (`self.trade_info = get_trade_status(self.trade_id, with_order=True)`) never printed, and the loop tail's `@872 JUMP_BACKWARD` printed as a re-materialised condition (`POP_JUMP_BACKWARD_IF_TRUE`, 5 instr) + `LOAD_CONST None/RETURN_VALUE` |
| `…etf_basket_order` | 756/756 0 / 2 / 1 / True | mixed, **net-zero** (del 11 = ins 11) | orig`@1328 LOAD_GLOBAL strategy_log` ‖ prod`@1380 LOAD_FAST …` (the 11-instr arm simply not there) | `else: strategy_log.warning('该股票【%s】行情数据异常'); return None` printed **after** the whole then-side (owner `IF_THEN_ELSE entry=568 then=[674…2496] else=[1328] merge=None`), so `@672 POP_JUMP_FORWARD_IF_FALSE` travels idx271→idx508 |
| `…etf_purchase_redemption` | 426/414 −12 / 5 / 0 / True | content-loss (del 12, ins 2) — **judge says `Different bytecode`, not control flow** | orig`@2274 LOAD_GLOBAL strategy_log` ‖ prod`@2274 LOAD_CONST 'list_info00orderstr…生成订单，订单号：'` | f-string literal prefix assembled out of pending-stack **names** (product line 1593), plus `' 数量：'`→`' 数量：order'`; 2 hidden 1-instr deletes (`@2312 LOAD_ATTR order_id`, `@2328 LOAD_ATTR symbol`) |
| `…rzrq_credit_order` | 780/780 0 / 0 / 1 / True | **pure-landing** | `@2368 JUMP_FORWARD` orig→idx490 (`@2534 LOAD_GLOBAL Order`) ‖ prod→idx485 (`@2506 LOAD_GLOBAL EntrustDirection`) | the SELL-arm tail (`entrust_direction=EntrustDirection.SELL; entrust_bs='2'`) must skip the BUY/`'1'` pair (idx485–489) which is the **tail of the other arm**; claiming region `IF_ELIF_CHAIN entry=2136 merge=None`, block 2506 is a bare `BASIC` child of `IF_THEN_ELSE entry=0 (merge=None)` |
| `…ipo_stocks_order` | 1181/1180 −1 / 1 / 3 / True | mixed | orig`@3574 JUMP_BACKWARD` ‖ prod`@3570 JUMP_FORWARD` | two of its three landings are the **same** `isinstance`-guard-fusion shape as `get_ipo_stocks` (`@2494 POP_JUMP_FORWARD_IF_TRUE` orig→idx485 body ‖ prod→idx475 `JUMP_BACKWARD`); the third landing is a shadow of the one dropped single-instruction `continue` block (orig idx717, owner_count = 3 nested regions) |
| `…get_ipo_stocks` | 481/481 0 / 0 / 1 / True | **pure-landing** | `@1108 POP_JUMP_FORWARD_IF_TRUE` orig→idx225 (`@1154 LOAD_GLOBAL str`) ‖ prod→idx215 (`@1130 JUMP_BACKWARD`) | original = `if not isinstance(market_type, list):` wrapping **two** sequential guard `if …: continue`; product (line 2408) prints `if isinstance(…) or (…): continue / elif (…): continue`. Owner `IF_THEN entry=998 cond=998 then=[1110,1118,1130,1132,1140,1152] merge=1154` — merge is declared **correctly** (= orig landing), so the deviation is generator-side |

## 3. Buckets (classification with counts)

| # | bucket (mechanism, named from block role) | units | n |
|---|---|---|---|
| B1 | **terminator printed before the remainder of its own suite ⇒ CPython ≥3.10 dead-code elimination deletes that remainder** (the lost text IS in the product source; the compiler drops it) | `_process_order`, `_process_cancel_order`, `_sync_worker` | **3** |
| B2 | **`WhileRegion` with `entry ≠ header_block`** (one-time pre-test) emitted as `while <cond>:` ⇒ back edge re-targets the condition block | `_process_tick_order` | 1 |
| B3 | **guard fusion / condition inversion**: `if not X: (if A: continue)(if B: continue)` emitted as `if X or A: continue / elif B: continue`, so the `X`-true edge lands on the shared arm tail instead of the post-guard join | `get_ipo_stocks`, `ipo_stocks_order` (2 of its 3 landings) | 2 |
| B4 | **`merge_block is None` on the region that owns the jumping tail** ⇒ the arm's forward jump lands on the next linear block instead of the post-arm join | `rzrq_credit_order` | 1 |
| B5 | **region arm emitted after its whole then-side** (content net-zero, one block relocated; only reachable as an analyzer/emission-order property, never as a landing constant) | `etf_basket_order` (alone), plus the 214-instruction component of `_sync_worker` | 1 (+1 shared) |
| B6 | **leading statement of a loop-header block never emitted** + loop tail re-materialised as a condition re-test instead of `JUMP_BACKWARD` | `_trade_status_handle` | 1 |
| B7 | **f-string literal prefix polluted with pending-stack names** (constant materialisation, CFG untouched) | `etf_purchase_redemption` | 1 |

**Distinct mechanisms = 7** (10 units = 3+1+2+1+1+1+1, with `_sync_worker` carrying both B1 and B5 symptoms).
**B1 covers the most units (3) and by far the most instruction mass** (−465, −293 and the DCE leg of −3).

## 4. Host per bucket (`file : function : line`)

| bucket | host |
|---|---|
| B1 | `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py : _generate_block_statements_body : 52557` — the role→`{'type':'Break'}` sites at `:53041-53056` (`_block_role in (BlockRole.BREAK, BlockRole.PURE_BREAK)` → `Break` at `:53051-53056`) and the sibling sites `:9148`, `:9185`, `:9610-9611`, `:9658-9668`; role side `core/cfg/region_analyzer.py : get_block_role / _annotate_if_structural_roles` (BlockRole.BREAK/PURE_BREAK/CONTINUE) |
| B2 | `core/cfg/region_ast_generator.py : _loop_generate_while : 6645` (`While` AST built at `:6878`, `:8230`; the `while True` + pre-test split sites `:6882-6883`). Declaration side `core/cfg/region_analyzer.py : _identify_loop_regions : 4644` (`LoopRegion.header_block` vs `entry`) |
| B3 | `core/cfg/region_ast_generator.py : _if_extract_cond_instructions : 17225` and `: _detect_if_region_as_while_loop : 14531` (`:14657` builds `While(test=_combined_cond …)`); analyzer side `core/cfg/region_analyzer.py : _identify_boolop_regions : 26260` (`IfRegion.inline_boolop_chains`) |
| B4 | `core/cfg/region_analyzer.py : _identify_conditional_regions : 18463` (IfRegion `merge_block` declaration; `IfRegion.merge_block` field at `:367`, `get_score_merge_block` at `:398`) |
| B5 | `core/cfg/region_ast_generator.py : _generate_block_statements_body : 52557` + the sequence-region arm ordering (the `else`-arm printed after all `then_blocks` of `IF_THEN_ELSE`); ordering inputs `:1485`, `:1891`, `:5407` |
| B6 | `core/cfg/region_ast_generator.py : _loop_generate_while : 6645` (header-block leading-statement emission) with `:53172`; back-edge site `:3419` / `:3613` (`_current_loop.header_block`, `condition_block`) |
| B7 | `core/cfg/region_ast_generator.py : _fstring_parts_from_segment : 49427` (pending-stack family `:43975`, `:44027-44088`, `__fstring_target__` `:4917`/`:44113`/`:45164`) + `: _try_wrap_fstring_pending_call : 49608`; print side `core/cfg/code_generator.py : JoinedStr : 3587` |

All hosts are named from measurement, **not patched**. UNTESTED: which branch inside each host fires for which unit (that needs the recording-`generated_blocks`/wrapped-dispatch stub run in the producing process, which I did not install — see §6).

## 5. Which buckets are mutually exclusive (and the evidence that two units do NOT share one)

* **B7 ⊥ everything else**: the external judge classes `etf_purchase_redemption` as `Different **bytecode**`; the other nine as `Different **control flow**`. No region/CFG criterion can flip B7 and no constant criterion can flip the other nine.
* **B1 ⊥ the other seven** by census: dead-suites after a terminator = `1 / 2 / 2` for the B1 trio and **`0` for all seven remaining units** (probe over the product AST). The B1 trio is also the only place where the lost content is present in the product **text** but absent from the product **bytecode**.
* **B2 ⊥ B3 ⊥ B4** — the three pure-landing units do **not** share one mechanism; three different region kinds, three different jump classes, three different declarations:
  * `_process_tick_order`: `WHILE_LOOP entry=114 header_block=130`, back edge `JUMP_BACKWARD`, and its code object has **0 IfRegions with `merge_block is None`** ⇒ a merge-declaration criterion cannot reach it at all.
  * `rzrq_credit_order`: `JUMP_FORWARD` from a tail block owned by `IF_ELIF_CHAIN entry=2136` **with `merge=None`** ⇒ declaration really is missing here.
  * `get_ipo_stocks`: owner `IF_THEN entry=998 merge=1154` — merge **present and equal to the original's landing**, yet the product lands on `1130`; the deviation is introduced by the printed `or`-fusion, i.e. generator-side. A "declare the merge correctly" patch would be a no-op for this unit (proof: the correct merge is already declared).
* **B5 ⊥ B3/B4**: `etf_basket_order` has a *content* move (delta 0 but `hunks=2`, 11 instr deleted and the same 11 inserted) while B3/B4 units are `hunks=0` — nothing moved there, only a target. Different code path (arm ordering vs merge/inversion).
* **B6 ⊥ B1**: `_trade_status_handle` loses a statement that is **absent from the product text** (`get_trade_status(self.trade_id, with_order=True)` appears nowhere in the function body) whereas B1's losses are text-present/DCE-deleted; and `dead_suites=0` on it.
* **`_sync_worker` is the only unit in two buckets** (B1 for the DCE leg, B5 for the 177/162-instruction relocation leg); its `POP_JUMP_FORWARD_IF_TRUE→IF_FALSE` leg at `@362` is a third symptom but it is inside the B5 window test.

## 6. The `merge_block is None` census (run as required)

Out-of-band process (`build_cfg` + `RegionAnalyzer(cfg).analyze()` on the **original** code objects; nothing generated, nothing written; only `r.blocks`/arms/`instructions` read, `successors` untouched):

| unit | regions | IfRegion | merge=None | of those, arm tail `JUMP_BACKWARD` |
|---|---|---|---|---|
| `_process_order` | 19 | 14 | **0** | 0 |
| `_process_tick_order` | 8 | 3 | **0** | 0 |
| `_process_cancel_order` | 15 | 10 | **0** | 0 |
| `_sync_worker` | 26 | 14 | **0** | 0 |
| `_trade_status_handle` | 6 | 3 | **0** | 0 |
| `etf_basket_order` | 60 | 42 | 4 | **2** (`entry=568` is the `IF_THEN_ELSE` that owns the relocated `else=[1328]`) |
| `etf_purchase_redemption` | 31 | 9 | 4 | 0 |
| `rzrq_credit_order` | 99 | 25 | 3 | 0 |
| `ipo_stocks_order` | 88 | 46 | 2 | 0 |
| `get_ipo_stocks` | 38 | 23 | 2 | 0 |

Reading: **the merge-less signature is absent on all five big-loss units and on `_process_tick_order`** — so it cannot be this file's shared axis, exactly the wizard/clock_worker pattern repeated. Where it is present, only two units have a *load-bearing* merge-less region (`rzrq_credit_order` = B4; `etf_basket_order` = B5's owner) and none of the others correlates.

## 7. Smallest bucket that could flip a FILE

A file flips only when **all** its units are Equal. `trade_live_broker.pyc` has 10 failing units spread over **all 7 buckets**, so:
* **no bucket in this file can flip a file by itself** — the smallest closing set for *this* file is **B1+B2+B3+B4+B5+B6+B7 (7 mechanisms)**, which buys 10 units and +1 file (118→128, 391→392).
* Highest yield per unit of mechanism: **B1 (3 units, −758 instructions of the file's loss)**; then B3 (2 units). Both are single-mechanism tickets.
* Cheapest file flips corpus-wide remain the six one-unit-away files (1 mechanism = 1 unit = 1 file) — the broker is the worst rate in the pool: 7 mechanisms per 1 file.

## 8. Explicit negatives

1. **No repo bytes were touched**: `git status --short -- core site-packages` empty at start and at end; the four landed hashes of §1 re-verified unchanged at session end; no `*OK.py` written into the repo; `gate_round.py`/`gate_chain.py` never run; no `git` write. **Mirror restored/unchanged**: `cp -r` once at 12:07, no write to `D:/Temp/r23d/wt/**` for the rest of the session (all instruments live in `D:/Temp/r23d/out/*.py`); zero `core/` patch, zero stub, therefore nothing to byte-revert.
2. **No stub/patch experiment was run.** Every census here is out-of-band and cannot perturb the product (products regenerated only with the pristine mirror). Consequently **no claim in §4 is "measured to fire"** — hosts are named from block role, region structure and emission-site grep; a proposal-style predicate (e.g. "emit `if <cond>: while True:` when `LoopRegion.entry is not header_block`" for B2) is **UNTESTED** and deliberately not booked.
3. **Ledger corrections against the round23 sealed table (measured today on landed bytes):**
   * `_trade_status_handle` is **del 10 / ins 7, delta −3** — not "del 18", and it shares nothing with the B1 trio.
   * `_process_order` / `_process_cancel_order` are **−465 / −293** (del 468 / del 297), and they do **not** need "a co-requisite #16 patch": their content is already printed and is removed by the *compiler*. A claim-site patch cannot recover text that DCE eats.
   * `etf_basket_order` is **1 alignment-mapped landing**, not 32 target diffs; `ipo_stocks_order` is **3 landings of which one is a shadow** of the deleted `continue`, not 35. Booking either count as defects overstates them by an order of magnitude (shift shadows).
   * `_sync_worker`'s chained-compare leg is real (`@362 IF_TRUE→IF_FALSE`) but its dominant diff is a **177↔162-instruction relocation plus one DCE'd return**, not "178/180 chain leg + relocation" alone.
4. **The generator-side landing channel stays closed**: all three pure-landing units are explained as (B2) header/entry declaration, (B4) missing merge declaration, (B3) arm ownership after a printed `or`-fusion — never as a landing constant, per the three prior falsifications.
5. **Ruler caveat worth registering**: `unit_diff.py --all` is documented in the module docstring but **never parsed** (`main()` reads only argv[1]/[2]/`--prod`), so the `min(...)==0 and max(...)<3` filter still hides hunks while `hunks=` counts them. I recovered the hidden hunks with my own dump (`D:/Temp/r23d/out/fulldump.py`): `etf_purchase_redemption` has 2 hidden 1-instruction deletes (`@2312 LOAD_ATTR order_id`, `@2328 LOAD_ATTR symbol`) and `ipo_stocks_order` has 1 (`@3574 JUMP_BACKWARD`). Any ticket sized off `hunks=`/printed-hunks alone is under-reading these two units.
6. **Nothing here is a fix.** No predicate in this doc was installed; no unit is claimed flipped; `118/128` stands as measured.

## 9. End-of-session integrity proof (re-run, not asserted)

| check | result |
|---|---|
| four landed core hashes re-read at session end | `4f295dfc6ebd2caa / ec6bd48826c65df9 / 7d8acab92ccc7782 / beeaf14435e22922` — **unchanged from §1** |
| `git status --short -- core site-packages scripts` | **empty** (zero repo byte written by me) |
| in-place broker product | `6a71fc95a5e6b388` = my mirror product, unchanged during the session |
| mirror re-check | 97 files compared repo↔mirror sha256[:16] again at the end → **mismatch = 0**, so the mirror was never instrumented (nothing to restore byte-exactly; it has been pristine since the single `cp -r` at 12:07) |
| HEAD movement during the session | `25fa7e7d → c4e790dd` — one **doc-only** commit by `r23a` (its own note states no repo byte was written; my four hashes confirm that). No measurement in this report is stale w.r.t. current landed bytes. |
| gate | never invoked (`gate_round.py` / `gate_chain.py` not run); the 402-file corpus gate is untouched |
| other engineers' dirs | `D:/Temp/r23a` not read |
| all commands | wall-clock ≤ 6.1 s each (longest: broker regeneration), far under the 300 s cap; every command used `python -X utf8`, `PYTHONIOENCODING` never set |

