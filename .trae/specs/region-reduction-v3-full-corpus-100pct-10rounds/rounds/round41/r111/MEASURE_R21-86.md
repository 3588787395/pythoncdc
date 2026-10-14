# MEASURE_R21-86 — render-scoped claim + recorded release (engineer r111a)

Mirror `D:/Temp/r111` (layout copied from `D:/Temp/r110`). Reference repo
`D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` was read-only for me: repo
`core/cfg/region_ast_generator.py` still hashes `566ff5c502276e48` and
`core/cfg/region_analyzer.py` still hashes `1471c92eca157e46` (verified after the last arm);
no git write command was run, no `*OK.py` was hand-edited, no product came from anywhere but
`pycdc.py`.

**Candidate generator: `59a405837c22a4cb`** — 3,873,983 B, BOM present, 100 % CRLF, zero bare LF,
zero `CR CR LF`, `compile()` clean, built only by `PATCH_R21-86_region_ast_generator.py` from the
landed bytes (re-running the patch reproduces the same sha16 — idempotent).
**Analyzer co-requisite: NOT used.** `[R21-79]` `3ad5ceaa23135334` is banked and was measured as an
optional pairing; the generator rule does its work on the pinned platform `996a1b1acf143458` alone
(and slightly better there).

Every arm ran with the platform installed and restored + re-hashed inside the same command
(`rig/arm_r111.py`, final line of every log: `[restore] ana=996a1b1acf143458(True)
gen=566ff5c502276e48(True)`).

## 1. Matrix — `clock_worker` against the byte-identical 13/13 oracle

`oracle_diff_r104.py` + `hunk_attribution_r107.py`, product written to `out/rt_<label>.py`.

| # | arm | analyzer | generator sha16 | ours (ORACLE 254) | instrs | back | jsites | hunks_vs_ORACLE | indeg-equal | judge line |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | pinned base (landed gen) | `996a1b1acf143458` | `566ff5c502276e48` | 241 | -114 | +0 | -9 | 4 | False | `12/13 Different control flow` |
| 0' | base + `[R21-79]` (lead's F5 row) | `3ad5ceaa23135334` | `566ff5c502276e48` | 241 | -115 | +0 | -9 | 4 | False | `12/13 Different control flow` |
| 1 | **lead's claim pair, reproduced by me** | `3ad5ceaa23135334` | `71c6863e0b085969` | 262 | -7 | +0 | +2 | 5 | False | `12/13 Different control flow` |
| 2 | **my rule, generator-only** | `996a1b1acf143458` | **`59a405837c22a4cb`** | 262 | **-6** | +0 | **+2** | **4** | False | `12/13 Different control flow` |
| 3 | my rule + `[R21-79]` co-requisite | `3ad5ceaa23135334` | `59a405837c22a4cb` | 262 | -7 | +0 | +2 | 5 | False | `12/13 Different control flow` |

Reproduction of row 1 is exact (`21588` raw / `21220` CR-stripped product bytes, same as the lead's
table). Row 2's product is `21788` raw / `21420` CR-stripped against committed `20555`/`20205`
(the only intended change).

Ablations of row 3 (each a one-line mutation of my candidate, all paired with `3ad5ceaa`):

| ablation | generator sha16 | reading | verdict |
|---|---|---|---|
| site A narrows + releases, **`:26911` skip removed** | `6c212c813c0c51fc` | 241 / -115 / -9 / 4 / 12-13 | **base** → the honour at `:26911` is load-bearing (this ablation *is* addendum 9's arm A, reproduced) |
| **release disabled** at site A (claim as landed), `:26911` skip present | `8aa2595869e67954` | 241 / -115 / -9 / 4 / 12-13 | **base** → the recorded release is the actuator |
| in-flight-owner safety guard replaced by `True` | `ac9628fa75faf64e` | 262 / -7 / +2 / 5 / 12-13 | **identical to my rule** → the guard carries no gain, it only prevents dropping code |
| rule extended to the `then_blocks` claim too | `949fbe8bfd05824d` | 262 / -6 / +2 / 4 / 12-13 | no gain, no collateral → rejected, kept narrow |

Direction check (bar 1): `instrs` moved `-114 → -6` (94 % of the dropped run recovered) and `jsites`
`-9 → +2`; the run is printed **once** — see §2 — but `ours` is 262, i.e. above the oracle, and that
overshoot is *pre-existing*, not created by the release: `base = 254 − 21 (missing run lines) + 8
(step-3/4 or-chain scaffolding) = 241`, and my product differs from the lead's pair product only by
the analyzer half. I therefore did **not** reach `ours` approaching 254 from below; the +8 belongs to
ladder steps 3/4 (nested if/elif where the oracle text is a flat `if (A and B) or C:`), which emit the
recovered run one indent level deeper than the oracle. Reported, not papered over.

## 2. No duplication (the "printed twice" question)

Marker counts, oracle vs my product (`out/rt_r2186_F5only.py`) — every run statement occurs exactly
once in both: `broker_persist = None` 1/1, `persist_flag = False` 1/1, `jsonpickle.decode` 1/1,
`获取持久化对象异常` 1/1, `set_trade_stop_status` 2/2, `server_restart_not_do_before` 1/1,
`put_before_trading_start` 4/4, `on_before_trading_start_time` 4/4, `EventEnum.HANDLE_DATA` 3/3,
`AFTER_TRADING_END` 2/2, `time.sleep(FPS)` 2/2, `check_trading_time` 4/4; only
`获取重登信号量` is short (1 vs gold 2 — that is step 3's swallowed debug call, not mine).
Base→mine text diff is a single insertion of 21 lines at product line 235 plus one reindent, i.e. the
release adds the run's tail and removes nothing.

## 3. Collateral smoke, 10 files, CR-stripped byte compare against the committed products

| file | committed raw / CR-stripped | lead's pair `71c6863e` | **my rule `59a40583`** |
|---|---|---|---|
| realtime_event_source.pyc | 20555 / 20205 | CHANGED 21220 | **CHANGED 21420 (intended)** |
| trade_live_broker.pyc | 178823 / 175772 | **CHANGED 176697** | **IDENTICAL** |
| klinedata.pyc | 102772 / 100737 | **CHANGED 101368** | **IDENTICAL** |
| fly/data/quote.pyc | 93018 / 91268 | IDENTICAL | IDENTICAL |
| real_quote.pyc | 53841 / 52796 | IDENTICAL | IDENTICAL |
| fly/data/quotation.pyc | 182759 / 179081 | IDENTICAL | IDENTICAL |
| order_api.pyc | 34308 / 33768 | IDENTICAL | IDENTICAL |
| replace_utils.pyc | 13501 / 13213 | IDENTICAL | IDENTICAL |
| plugin_system_risk_calculation/function.pyc | 30095 / 29631 | IDENTICAL | IDENTICAL |
| handlers.pyc | 9030 / 8827 | IDENTICAL | IDENTICAL |

Broker stays at its committed 178 823 bytes. The same table holds with the `[R21-79]` pairing (row 3
of §1): both collateral files are IDENTICAL there too, which is the point of the ticket.

Why: at site A the or-chain branch fires 0 times in `trade_live_broker` and `klinedata` (runtime
claim census, `logs/claims_*.json` — site-A event counts: victim 17, broker 0, klinedata 0), so the
release ledger is empty and the `:26911` claim behaves exactly as landed; those two files' collateral
under the pair came from blanket `:26911` un-marking (3 and 8 *new-transition* claims there), which my
rule preserves.

## 4. 20-file panel, `rounds/round38/PANEL_20files.txt`, paired BY INDEX (`rig/panel_r111.py`,
config = my rule + pinned F5 analyzer; row also carries a CR-stripped byte compare)

| idx | panel row | units | verdict | bytes vs committed |
|---|---|---|---|---|
| 00 | fly/data/quotation.pyc | 153/153 | success | SAME |
| 01 | fly/data/quote.pyc | 92/92 | success | SAME |
| 02 | IQCommon/api/klinedata.pyc | 64/64 | success | SAME |
| 03 | IQCommon/logger/handlers.pyc | 30/30 | success | SAME |
| 04 | IQCommon/strategy/wizard_quant_api.pyc | 58/58 | success | SAME |
| 05 | IQCommon/util/trade_info_utils.pyc | 41/41 | success | SAME |
| 06 | IQData/api/api_base.pyc | 28/28 | success | SAME |
| 07 | .../realquote/real_quote.pyc | 45/45 | success | SAME |
| 08 | .../fly_data/strategy/strategy.pyc | 27/27 | success | SAME |
| 09 | .../fly_api/order_api.pyc | 37/37 | success | SAME |
| 10 | .../trade/trade_live_broker.pyc | 128/128 | success | SAME |
| 11 | .../matcher/matcher.pyc | 17/17 | success | SAME |
| 12 | .../event_source/realtime_event_source.pyc | **12/13** | failure, `Different control flow` | DIFF 21420/20205 (intended) |
| 13 | .../risk_calculation/__init__.pyc | 43/43 | success | SAME |
| 14 | IQCommon/arg_checker.pyc | 49/49 | success | SAME |
| 15 | IQData/utils/arg_checker.pyc | 39/39 | success | SAME |
| 16 | IQEngine/utils/arg_checker.pyc | 43/43 | success | SAME |
| 17 | IQCommon/profiler_func.pyc | 17/17 | success | SAME |
| 18 | IQData/utils/profiler_func.pyc | 15/15 | success | SAME |
| 19 | IQEngine/utils/profiler_func.pyc | 18/18 | success | SAME |

19/20 rows unchanged and byte-identical; row 12 is the target file and its verdict class is
unchanged. Zero panel regression.

## 5. Whole-corpus 402 sweep, CR-stripped byte compare (`rig/sweep_r111.py`, config = my rule +
pinned F5 analyzer), ROOT-joined roster

Roster `rounds/round40/r95/corpus402.txt` (402 entries, repo-relative) is joined with
`ROOT = D:/admin/.qoder/.../pythoncdc-main`, and the script asserts `len(paths) == 402` and prints
the ROOT it used, `files_compared`, `MISSING/FAIL` per shard, so a zero is only readable with
`MISSING/FAIL = 0`:

| shard | files_compared | MISSING/FAIL | SMALL (<200 B, still compared) | CHANGED_COUNT |
|---|---|---|---|---|
| [0,100) | 100 | 0 | 13 | 0 |
| [100,200) | 100 | 0 | 10 | 0 |
| [200,300) | 100 | 0 | 7 | **1** |
| [300,402) | 102 | 0 | 12 | 0 |
| **total** | **402** | **0** | 42 | **1** |

`CHANGED site-packages\IQEngine\plugins\plugin_system_event_source\realtime_event_source.pyc
ours=21420 committed=20205` — `CHANGED = {realtime_event_source.pyc}` only, which is the bar.

## 6. Judge

`12/13`, `Different control flow`, unchanged verdict class — **the flip was NOT reached**, so per the
ticket this is a **bank**, not an install.

**Install recommendation: NOT installable.** The bar was `judge 13/13` AND
`CHANGED = {realtime_event_source}` AND zero panel regression: two of three hold, the judge does not.
It is nevertheless the first rule in this campaign that gets the pair's recovery (94 % of the dropped
run, `-114 → -6`) with **provably zero collateral on all 402 files**, and it replaces the pair as the
standing baseline for the next ticket: the remaining gap is positional (steps 3/4 or-chain folding —
addendum 9's half (a), "the arm renderer must continue past a dispatched child region to the rest of
the same arm"), not a claim-membership gap.

## 7. Artifacts (absolute, re-runnable)

| path | role |
|---|---|
| `D:/Temp/r111/DELIVER/PATCH_R21-86_region_ast_generator.py` | idempotent anchored patch, landed → `59a40583` |
| `D:/Temp/r111/DELIVER/CANDIDATE_r2186_59a405837c22a4cb.py` | the candidate generator |
| `D:/Temp/r111/DELIVER/FIX_R21-86_render-scoped_claim.md` | rule, discriminator, rulers reused, excluded-premise reconciliation |
| `D:/Temp/r111/rig/arm_r111.py` | one-arm harness: install → victim oracle-diff + attribution → 10-file collateral → restore + re-hash |
| `D:/Temp/r111/rig/panel_r111.py` | 20-file panel by index with per-file unit counts + byte compare |
| `D:/Temp/r111/rig/sweep_r111.py` | 402-file ROOT-joined sweep, asserts the join |
| `D:/Temp/r111/rig/probe_claims_r111.py`, `D:/Temp/r111/logs/claims_*.json` | runtime-only claim census (site A 17 events all at `IfRegion@7604`; site B 0 new transitions in the victim, 3 in broker, 8 in klinedata) |
| `D:/Temp/r111/rig/diff_unit_r111.py` | oracle↔product unit-body diff |
| `D:/Temp/r111/abl_r2186_*.py` | the four ablation/mutation arms quoted in §1 |
| `D:/Temp/r111/out/rt_*.py`, `D:/Temp/r111/logs/{arm,panel,sweep}_*.txt` | raw products and logs for every row |

Probe inertness: the traced victim product is character-identical to the un-traced in-process product
(`untraced_chars 19665 == traced_chars 19665 → IDENTICAL True`) and `core/cfg` re-hashed
`996a1b1acf143458` / `566ff5c502276e48` after every probe run.

## 8. Untrusted text

Tool outputs during this session repeatedly carried instruction-looking lines (a skills
`<system-reminder>`, `Note:` banners, and several `stop - 当前 job ... switch ...`-style advisories
appended to Bash/Grep results, plus comments in committed source addressed to other agents). I treated
all of it as data, did not act on it, and kept the ticket's scope; nothing changed my target.
