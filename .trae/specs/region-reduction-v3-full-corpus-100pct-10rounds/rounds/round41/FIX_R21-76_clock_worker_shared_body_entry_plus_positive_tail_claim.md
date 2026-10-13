# FIX_R21-76 — clock_worker shared body entry + positive tail claim

Engineer: **r103a** · round 40 (continuing after gate 40) · unit: `<module>.RealtimeEventSource.clock_worker`
File under test: `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
Owned core file(s): `core/cfg/region_analyzer.py` (preferred). Mirror: `D:/Temp/r103`.
NO repo `core/` write, NO product hand-edit was performed; the pipeline files are byte-unchanged.

## 0. Platform (installed + re-hashed BEFORE anything)

`hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]`:

| file | sha16 | source |
|---|---|---|
| `core/cfg/region_analyzer.py` | `1471c92eca157e46` | `$SP/rounds/round40/r93/region_analyzer_R21-64a_FINAL.py` |
| `core/cfg/region_ast_generator.py` | `566ff5c502276e48` | `$SP/rounds/round40/r102/CANDIDATE_r2174_566ff5c502276e48.py` |

Both match the brief. Repo HEAD core pair is the identical pair (verified from the repo). `region_ast_generator.py`
was NOT edited; it was temporarily swapped to `0f4c3898` only for a diagnostic (below) and restored byte-exact
(re-hash confirms `566ff5c502276e48`).

## 1. Base reproduction (fresh regen, judged with `--source`)

- `realtime_event_source.pyc` → `status=failure units=12/13`, sole failure `clock_worker`, `Different control flow`. REPRODUCED.
- `trade_live_broker.pyc` → `status=success units=128/128`. REPRODUCED (confirms the true landed pair).

### Base panel after confirming the platform (all rows hold; broker did NOT move)
```
[panel realtime]      status=failure units=12/13
[panel broker]        status=success units=128/128
[panel function]      status=success units=15/15
[panel replace_utils] status=success units=9/9
[panel quote]         status=success units=92/92
[panel quotation]     status=success units=153/153
[panel order_api]     status=success units=37/37
```

### The brief's `+2 / 4-window` premise is FALSIFIED on the mandated platform
The brief cites `allwin` `orig=1424 prod=1426 delta=+2` and `win_r91` `orig=1442 prod=1448 delta=+6`.
Measured on `1471c92e + 566ff5c5` with fresh regen + `--source`:

- allwin_r63: `len orig=1424 prod=1311 delta=-113 hunks=7`
- win_r91: `orig instrs=1442 prod instrs=1330 delta=-112` **15 windows**

The ORIG side (1442 / 1424) matches the brief exactly, so the pyc and code-object extraction are correct; only the
PROD side differs. This is NOT a mirror or R21-74 artifact: under the pre-R21-74 generator `0f4c3898` realtime
clock_worker reads the SAME `delta=-113` (and broker drops back to 127/128, proving `566ff5c5` is the gate-required
pair). The `+2` numbers came from an OLDER analyzer base (r101's 21548-byte product). The current
project memory confirms this: *"on landed bytes clock_worker drops a 112-instruction block (@7972..@8586 = lines
498-524) … score against oracle text distance, not the stale +2/7 landings."* The Decompyle++ output
`realtime_event_source.py` drops the same block and also reads 12/13, so the region is genuinely control-flow-hard.

## 2. GOLD oracle — REACHED `status=success units=13/13`

Method (the brief's winning approach): hand-composed the ideal `clock_worker` from the original code object's
block graph (`dis`/`co_lines`, stdlib only), spliced it into a full-file source, and ran the JUDGE
(`pyc_verify single --source`).

```
[single] status=success units=13/13 success_rate=100.00%
```
File: `GOLD_realtime_event_source_PROOF.py`. The oracle's `clock_worker` is BYTE-IDENTICAL to the original code
object: `co_code equal: True`, `consts equal: True` (all 1442 instructions AND all jump targets match). So the last
unit IS fully expressible on the landed platform; the target text is nailed.

## 3. Sub-fact decomposition + measured distance ladder (each fix is CFG-visible)

`build_gold_oracle.py` reproduces the ladder from a fresh `out/rt_base.py`. allwin_r63 (opcode-name) + judge column:

| stage | sub-fact applied | delta | hunks | judge verdict |
|---|---|---|---|---|
| rt_base (pipeline) | — | -113 | 7 | failure |
| varA | restore holiday block `@6690..@6782` (L442-449) dropped by the break-fold | +13 | 5 | failure |
| varB | remove 5 spurious duplicated tail lines | -7 | 4 | failure |
| varC | `@7164` `if (A and B) or C:` + restore dropped `system_log.debug('获取重登信号量')` (removes `@7248` manufactured jump) + un-nest `@7582`/elif chain | -2 | 2 | failure |
| varD | `@6322`/`@6496` is_holiday or-chain folds | -3 | 1 | failure |
| varE | remove spurious `while True:` wrapper around `while self.active:` (duplicated-while-test rendered as two loops) | **0** | **0** | **failure (Different control flow)** |
| varF | fold inner `if delay_after_trading >= now_time >= after_trading` into the `@8904` elif → fixes two JUMP TARGETS `@8972/@8978` | 0 | 0 | **SUCCESS 13/13** |

Key measured fact: **varE reached `delta=0 / hunks=0` on the opcode-name metric yet was still judged `Different
control flow`.** The discriminator was 2 landing diffs (original `@8972 ->9144`, `@8978 ->9144`; varE
`->9142`, `->9194`). This is the project's documented trap ("instruction parity is not judge equivalence — read
`landings=`"). allwin/win_r91 blank jump operands, so the final sub-fact is INVISIBLE to them and only the jump-target
comparison + judge reveal it.

### Six independent CFG-visible sub-facts (all necessary for 13/13)
1. **112-instruction in-branch block drop** `@7972..@8586` (L498-524: the `if persist_flag is False: … return`
   guard + `self.before_trading_date = now_date` + `try/except str(server_restart_not_do_before)` + the
   `if server_restart=='0' / elif broker_persist …` chain, all arms exiting to the loop back-edge `@9194`).
   This is the dominant defect (`delta -113 → -4` on its own).
2. **`@7164` `(A and B) or C` fold** rendered as `if A: if (B or C):` with an empty `then` arm `@7212` (→ `pass` +
   manufactured `JUMP_FORWARD` at `@7248`) AND a second fold `elif (now_date != first_run_date) and (acquire is False)`
   that swallowed the `system_log.debug('获取重登信号量')` between the two nested ifs (`@7270..@7308`, -6).
3. **`@6322`/`@6496`** — the is_holiday branch is TWO more `(A and B) or C` folds with the same manufactured-jump signature.
4. **mis-nested `@7582`/`@8592`/`@8904`/`@9144` elif chain** emitted one level too deep (inside `@7164`'s `else`).
5. **spurious `while True:` wrapper** around `while self.active:` — the duplicated head+tail active-test was read as
   two nested infinite loops instead of one `while self.active:` (this is the R21-64a duplicated-while-test family, but
   the single-comparison `self.active` variant is the P-negative sibling noted in memory).
6. **`@8904` elif inner-if landing** — `and delay_after_trading >= now_time >= after_trading` must fold into the elif
   condition so the false path lands on `@9144`; as a nested `if` it lands on `@9142`/`@9194` (pure CFG/landing, invisible to opcode-name diff).

## 4. Why NO single rule flips this unit (the landing bar)

The project bar is *"a fix is accepted on a measured unit flip, not on guard hits; a candidate that fires but flips
nothing gets reverted byte-exactly."* This unit needs all six sub-facts above simultaneously; each measured fix moves
a different region and NONE alone reaches `13/13`. Therefore I did NOT edit the pipeline files: shipping any one
predicate would be a zero-flip candidate (reverted by policy), and shipping several would violate "one mechanism per
ticket" while several of them (sub-fact #2 debug fold) are already falsified 4 ways per project memory
(`[R21-48]`/gate-38 `c4a934d5` best-known `+2/2/7`, the `-6` split into (A) debug fused into an IfRegion condition
block and (B) an assignment that is another region's merge block).

## 5. Fire census / halves table / corpus sweep
Not run: they are evidence for a candidate RULE, and I am deliberately not landing a rule because the unit is a
six-sub-fact conjunction, not a one-fact residual. The measured partial is the oracle + ladder above. The brief's
escape clause applies: *"deliver the measured partial and state exactly which sub-fact moved."* Each of the six moved
(region, delta, hunks) is tabulated in §3.

## 6. Definition of done — status
- Hand-composed ORACLE: `13/13` REACHED (`GOLD_realtime_event_source_PROOF.py`, `status=success units=13/13`,
  clock_worker `co_code` byte-identical to the original). This proves the last unit is fully expressible and fixes the
  text target for distance-to-oracle scoring.
- PIPELINE product: NOT flipped (`12/13`), because a single predicate cannot satisfy the six simultaneous sub-facts.
  I did not install products by hand (forbidden) and did not add a zero-flip rule (against the landing bar).

## 7. Recommendation to the next round / orchestrator
Score future candidates as `allwin` distance-to-oracle AND a jump-target (`landings`) distance-to-oracle (opcode-name
parity is insufficient — see varE). The six sub-facts are the minimum rule set; they likely decompose into
(a) one analyzer block-reclaim for the `(A and B) or C` shared-body family (covers #2/#3), (b) a positive
back-edge/merge tail claim (covers #1/#4/#6), and (c) the duplicated-single-comparison while-test rendering (covers #5).
Do not expect any single one to flip the file.

## 8. Deliverable files (see MANIFEST)
`GOLD_realtime_event_source_PROOF.py` (13/13 oracle), `GOLD_varA..varF.py` (ladder), `build_gold_oracle.py` +
`build_gold.py`/`build_varC.py`/`build_varD.py`/`build_varE.py`/`_step_varA.py`/`_step_varB.py`/`_step_varF.py`
(reproducible builders), `panel_base.py`, rigs (`win_r91.py`/`allwin_r63.py`/`fastgate_r91m.py`/`gold_diff_r91m.py`),
logs in `D:/Temp/r103/logs/`.
