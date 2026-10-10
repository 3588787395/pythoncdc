# ADJUDICATION (provisional) — R21-13 candidate measured by the orchestrator, 2026-10-10 13:2x

Status of the evidence: **mid-flight**. `D:/Temp/r29/DELIVER/` was still empty when these readings
were taken, and the engineer's mirror file hash had settled at `e8e8a9b6b88080b9` (unchanged across
~7 minutes). Per the standing rule a mid-flight snapshot is not a verdict, so nothing was installed;
this note exists so the install can be attributed and cross-checked against the engineer's own
census when its FIX doc arrives.

## How I measured
Own throwaway mirror `D:/Temp/r30chk`, built from repo bytes and *proven* to reproduce the sealed
product (`plugin_system_risk_calculation/__init__OK.py` regenerated there was `cmp`-IDENTICAL before
any patch). Installed the candidate as a whole file, re-verified `py_compile` OK, then judged each
file with `scripts/pyc_verify.py single <abs pyc> --source <that product>` (Windows-style absolute
paths — MSYS-style `/d/...` silently produced "缺少产物", a rig trap, not a result).

Candidate content vs sealed `c0744254:core/cfg/region_ast_generator.py`: **+83 / −7 lines**. It adds
`_inline_and_chain_exits_agree(chain_blocks)` (documented as read-only: reads jump targets only, marks
no `generated_blocks`), a `[R21-13 判据]` veto in `_if_generate_elif_chain` before the
`inline_boolop_chains` 'and' record is lifted into the elif test, and a `_r2113_legs_back` path that
returns the leg blocks to the arm body via `region.elif_bodies[0] + legs` sorted by `start_offset`.
Mechanism matches the ticket's premise (the analyzer records an `or` chain's first leg as an `and`
conjunction; disagreeing short-circuit exits falsify it, so the lift is refused).

**Install hazard:** the candidate file is **CRLF** (59 767 CR bytes) while the repo file is LF-only
(0 CR). A naive whole-file install would rewrite every line of a 59 747-line file. On install,
transplant the added/removed line ranges onto the sealed LF bytes (or normalise the candidate to LF)
and then verify `git diff --stat` shows only the intended line count.

## Readings under the candidate
| file | sealed (gate 28) | under candidate | verdict |
|---|---|---|---|
| `IQCommon/strategy/wizard_quant_api.pyc` | 57/58 | **58/58 status=success** | **FILE FLIP** |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 44/45 | **45/45 status=success** | **FILE FLIP** |
| `fly/data/quotation.pyc` (sentinel) | 153/153 | 153/153, product 182 759 B = sealed size | no change |
| `IQEngine/.../fly_api/order_api.pyc` | 37/37 | 37/37 | no change |
| `IQEngine/.../matcher/matcher.pyc` | 17/17 | 17/17 | no change |
| `IQData/api/api_base.pyc` | 27/28 | 27/28 | no change (product bytes DIFFER) |
| `IQEngine/.../strategy/strategy.pyc` | 26/27 | 26/27 | no change (bytes DIFFER) |
| `IQCommon/logger/handlers.pyc` | 29/30 | 29/30 | no change (bytes DIFFER) |
| `IQCommon/api/klinedata.pyc` | 63/64 | 63/64 | no change (bytes DIFFER) |
| `fly/data/quote.pyc` | 91/92 | 91/92 | no change |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | 38/41 | no change |
| `IQEngine/.../plugin_system_risk_calculation/__init__.pyc` | 42/43 | 42/43 | no change |
| `IQEngine/.../realtime_event_source.pyc` | 12/13 | 12/13 | no change |
| `IQEngine/.../trade_live_broker.pyc` | 121/128 | 121/128 | no change |

Per-unit acceptance lines quoted from the rig:
```
wizard_quant_api  <module>.filter_desicion                 len orig=195 prod=195 delta=0 hunks=0 landings=0 judge_diff=False
real_quote        <module>.RealQuoteData.get_real_minute_kline len orig=279 prod=279 delta=0 hunks=0 landings=0 judge_diff=False
```

## Expected gate 29 reading if this is installed alone
units `6598 -> 6600` of 6617, files `391 -> 393` of 402, residual files `11 -> 9`,
residual units `19 -> 17`, with `regen ok=402 bad=0`, `文件级回退=0`, `UNIT_REGRESSIONS=0`.
Note the criterion is NOT surgical at the byte level — four panel files change product bytes while
their unit counts stay equal, so the gate (not this panel) is what must certify that no other file of
the 402 regresses. That is also why the engineer's own fire-census number is still required before
claiming the criterion is narrow.
