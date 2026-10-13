# FIX_R21-73 (WIP) — clock_worker: shared body entry @7248 wrongly claimed as elif_conditions[0]

Engineer r101a, round 40. Scope: `core/cfg/region_analyzer.py` ONLY (generator untouched;
r99a/r100a own `region_ast_generator.py` for `_sync_worker`). Mirror `D:/Temp/r101`.
Nothing installed. Deliverable = patch + measurements.

## 0. Platform certification (my own bytes, hashes verified first)

Mirror base installed from repo HEAD:
* `core/cfg/region_analyzer.py` sha256[:16] = **`842e2748bcdfeb66`** (landed, repo working tree)
* `core/cfg/region_ast_generator.py` sha256[:16] = **`675ec7afa414bbb5`**
  (= `rounds/round40/r92/CANDIDATE_r2163_675ec7afa414bbb5.py`, `[R21-63]`)
* NOT used: `db1f0e96072cdcb3` (chain base, regresses `function.pyc`).
* runtime CPython 3.11.7. Judge: `python -X utf8 scripts/pyc_verify.py single <pyc> --source <fresh product>`.

| file | expected | measured on my mirror | log |
|---|---|---|---|
| `plugin_system_risk_calculation/function.pyc` | 15/15 | **15/15 status=success** | `work/LOG_r101a_base_function.txt` |
| `IQCommon/util/replace_utils.pyc` | 9/9 | **9/9 status=success** | `work/LOG_r101a_base_replace.txt` |
| `plugin_system_trade/trade_live_broker.pyc` | 127/128, `_process_order` Equal | **127/128, sole failure `<module>.TradeLiveBroker._sync_worker: Different control flow`** ⇒ `_process_order` Equal | `work/LOG_r101a_base_broker.txt` |
| `plugin_system_event_source/realtime_event_source.pyc` | 12/13 | **12/13, sole failure `<module>.RealtimeEventSource.clock_worker: Different control flow`** | `work/LOG_r101a_base_realtime.txt` |

**clock_worker residual, both 口径 (NOT interchangeable):**
* `allwin_r63` / `unit_diff` (drop NOP/CACHE/EXTENDED_ARG): `len orig=1424 prod=1426 delta=+2`,
  `hunks=2`, `landings=7`. Insert-only: `#1 insert orig[1046 @7248] +1`, `#2 insert orig[1099 @7582] +1`.
* `win_r91` (opcode-name-only, keeps EXTENDED_ARG): `orig=1442 prod=1448 delta=+6`,
  **4 windows, all inserts**: `@7184 +1, @7248 +2, @7582 +2, @7602 +1`.
  ⇒ the same defect: two manufactured `JUMP_FORWARD`s (`@7252`, `@7590`) + the 4 `EXTENDED_ARG`s they force.

7 landings (unit_diff, verbatim from `LOG_r101a_base_realtime.txt` run, identical to r97a §2).

## 1. Ownership facts RE-MEASURED on my bytes (read-only dump AFTER analysis, `dump101.py`)

`work/LOG_r101a_dump_base.txt`. Block graph (original numbering):

```
@7164 tail=POP_JUMP_FORWARD_IF_FALSE succ=[7186, 7216]    leg A test
@7186 tail=POP_JUMP_FORWARD_IF_FALSE succ=[7202, 7214]    leg B test   == chain condition_block
@7202 tail=POP_JUMP_FORWARD_IF_TRUE  succ=[7212, 7248]    leg B's jump
@7212 tail=JUMP_FORWARD              succ=[7216]          bare jump block (arm0 "body")
@7214 tail=POP_TOP                   succ=[7216]
@7216 tail=POP_JUMP_FORWARD_IF_FALSE succ=[7248, 7582]    leg C test == chain merge == sibling cond
@7248 tail=POP_JUMP_FORWARD_IF_FALSE succ=[7270, 7492]    SHARED BODY ENTRY (leg D) == elif_conditions[0]
@7270 ..leg E test
@7492 tail=STORE_ATTR                succ=[7582]          else body, falls through to sibling stmt
@7582 tail=POP_JUMP_FORWARD_IF_FALSE succ=[7604, 7634]    statement 2's first block
```

`IF_ELIF_CHAIN` `condition_block=@7186` `merge_block=@7216`:
* `then_blocks = [7212]` — arm 0's declared body is the bare jump block only ⇒ rendered `pass` + manufactured jump.
* `else_blocks[0] = 7248` AND `elif_conditions = [7248]` — **@7248 double-claimed**.
* `elif_bodies = [[7372, 7488]]`, `inline_boolop_chains = {'and': [@7248, @7270]}` (only D∧E mounted).
* `elif_final_else` = 43 blocks, including `7582` (a LATER SIBLING statement's first block) and
  `9144` (the loop body's tail statement `time.sleep(FPS)`).
Sibling `IF_THEN entry=@7216 merge=@7582 then_blocks=[7248,7270,7372,7488,7492]` — @7248 is ALSO that
region's first then-block. Confirms r97a §3.1 byte-for-byte.

## 2. Implementation — [R21-73] re-designation in `region_analyzer.py`

Predicate C, keyed exactly as censused, implemented inside `_check_elif_chain` (top-level
call only, guarded `header_ is block`): fire when
(i) the chain's declared arm body is a single bare-jump block (`len(then_blocks)==1`, tail
`JUMP_FORWARD/JUMP_ABSOLUTE` onto `merge_`), (ii) `merge_` is itself an `IF_FALSE` conditional
test block, (iii) `merge_`'s non-jump, non-exception fall-through successor **is** the `first_else`
about to be claimed as `elif_conditions[0]`, and (iv) `not _boolop_shared_target_is_join(first_else,
(header_, merge_))` — the **landed** join discriminator (region_analyzer.py:31163) proves `first_else`
is entered only by conditional-test edges ⇒ it is a BODY ENTRY, not a join. Reuses landed machinery;
no new offsets/names/counters/thresholds.

On fire the empty-elif reduction returns
`{'conditions': [], 'bodies': [], 'final_else': [], 'inline_boolop_chains': {}, 'r73_body_entry_reject': True}`
so `@7248` is dropped from `elif_conditions`; a second gated edit after `elif_info = _check_elif_chain(...)`
sets `else_blocks = []` so the chain releases the swallowed tail blocks. Candidate `c93e8994893ee530`
(built byte-exactly from landed `842e2748bcdfeb66` by `BUILD_CANDIDATE_r2173.py`). BOM+CRLF intact
(`\r\r\n`==0, bare-LF==0), py_compile PASS.

## 3. Re-measured ownership after the re-designation (read-only dump `LOG_r101a_dump_after.txt`)

At `@7186` chain: `elif_conditions` `[7248] → []` and `elif_final_else` (43 blocks) `→ []`. The
double-claim on `@7248` is gone from the elif arm (it remains only in `@7216`'s own region then_blocks).
Predicate C fired on exactly one region — confirmed by the 402-file sweep (section 5).

## 4. THE TRANSITIVITY MEASUREMENT (step 4 — r97a never ran it) — MEASURED NEGATIVE

**No. Removing the double claim does NOT re-anchor `@7582` and the loop-tail `@9144` transitively —
it collapses them.** Both variants land on the identical product:

| stage | allwin/unit_diff 口径 | hunks | landings | judge |
|---|---|---|---|---|
| base (`675ec`+`842e`) | `orig=1424 prod=1426 delta=+2` | 2 | 7 | Different control flow, 12/13 |
| reject-chain (`return None`) | `prod=1155 **delta=−269**` | 4 | 2 | Different control flow, 12/13 |
| empty-elif + release-tail (`c93e89`) | `prod=1155 **delta=−269**` | 4 | 2 | Different control flow, 12/13 |

win_r91 口径 on base unchanged (`orig=1442 prod=1448`, 4 windows all-insert); the after variants are
reported on allwin/unit_diff because win_r91's co-name find cannot pair the −269 product. The −269 is
THREE deletions of whole statement runs: `@7582..@7836` (−54), `@7960..@8276` (−55), `@8282..@9192`
(−160) = statement 2 + the loop-tail `time.sleep(FPS)` + intervening body. They **vanish from the AST**.

Root cause (measured, `LOG_r101a_dump_after.txt`): the blocks `@7582..@9144` are today emitted ONLY
*because* the over-absorbing `elif_final_else` carries them. Once the elif is stripped — with or
without `else_blocks=[]` — neither the chain (no final_else to render) nor the parent `@7164`
sequential path (which does not reclaim them) emits them. The generator renders the region body
structurally; there is **no analyzer field that both strips the `@7248` claim and re-anchors the tail
statements for emission**. This is the exact `no-landing-channel-in-generator` wall and the −269/−274
over-fire class the brief warned about.

**Verdict on "one rule or two":** clock_worker is **TWO rules**. Rule 1 (predicate C re-designation)
is necessary but on its own regresses the unit; rule 2 (a generator-side re-anchor of the region-end
label to the tail-statement block) is required and is NOT in my file scope. I did not reach 13/13.
The partial bar (`landings 7→≤3, hunks 2→≤1, delta +2→≤+1`) was **not** met — it went the wrong way
(delta +2 → −269), so this candidate is a measured negative, not a banked co-requisite toward a flip.
It is banked only as proof that rule 1 alone is insufficient and that the loss channel is the tail.

## 5. No-regression panel + 402-product sweep (both variants)

Panel judged with `python -X utf8 scripts/pyc_verify.py single <pyc> --source <fresh product>`.
`realtime_event_source` regressed inside the file (clock_worker +2→−269) but stays 12/13 units; all
other panel files unchanged on the patched analyzer:

| file | base | patched (`036f39`/`c93e89`) |
|---|---|---|
| `plugin_system_risk_calculation/function.pyc` | 15/15 | **15/15** |
| `IQCommon/util/replace_utils.pyc` | 9/9 | **9/9** |
| `plugin_system_trade/trade_live_broker.pyc` | 127/128 (`_sync_worker` sole fail ⇒ `_process_order` Equal) | **127/128**, same sole fail |
| `fly/data/quote.pyc` | 92/92 | **92/92** |
| `fly/data/quotation.pyc` | 153/153 | **153/153** |
| `plugin_fly_data/fly_api/order_api.pyc` | 37/37 | **37/37** |
| `arg_checker` (IQCommon/IQData/IQEngine) | 49/39/43 | **49/39/43** |
| `profiler_func` (IQCommon/IQData/IQEngine) | 17/15/18 | **17/15/18** |

The two canary families the elif-collection path historically over-fired into are **clean**.
(Logs `LOG_r101a_panel_light.txt`, `LOG_r101a_panel_heavy.txt`, `LOG_r101a_panel_c93e_light.txt`;
an earlier backgrounded combined panel read 13 REGEN-FAIL — a process-contention artifact proven
by re-running every one of them successfully serially.)

**Mandatory 402-product CR-stripped sweep** (`git archive HEAD site-packages | tar -x` → `head_sp`,
regen each product in-mirror, strip CR, `cmp`; never against checkout): **`same=401 changed=1`**
(`realtime_event_source.pyc` only, 20205 → 17730 bytes) — `newprod=0 nooutput=0`. Predicate C fires
on exactly one region in one file, zero collateral, confirmed corpus-wide.
(Log `LOG_r101a_sweep_c0.txt` `changed=1 … NEXT=372`, `LOG_r101a_sweep_c372.txt` `changed=0 DONE`.)

## 6. Deliverables (`D:/Temp/r101/DELIVER`)
`FIX_R21-73_clock_worker_shared_body_entry_claim.md` (this), `CANDIDATE_r2173_c93e8994893ee530.py`
(full analyzer, sha256[:16] `c93e8994893ee530`), `BUILD_CANDIDATE_r2173.py` (byte-exact reproduction
from landed `842e2748bcdfeb66`, asserts `c93e8994893ee530`), before/after ownership dumps, panel +
sweep logs. Nothing installed; mirror analyzer reverted to landed `842e2748bcdfeb66`. The campaign is
not complete: `realtime_event_source` remains 12/13 and `trade_live_broker` 127/128.

