# Certified 20-file panel baseline (sealed gate-31 bytes, measured 02:36–02:41)

Run: `python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r30chk sealbase 0 20`, mirror re-seeded from the repo
(generator `37d9fecb893704ac`, analyzer `35e227ac3e7b25af`). Every row is regen → `cmp` against the
on-disk product → `pyc_verify … --source`.

**`SAME` on all 20 rows**: a fresh regeneration from the sealed sources reproduces every one of these 20
committed products byte-for-byte. That is simultaneously the freshness proof for the adjudication mirror and
the certification of the baseline below — this is what later candidate reads are compared against.
Fifteen of the twenty are at full count; the five red ones are rows 2, 4, 6, 11 and 13, and their shortfalls
(1 + 1 + 1 + 7 + 1) are exactly the 11 residual units in `RESIDUAL_ROUND31.md`.

| # | file | units | product bytes | state |
|---|---|---|---|---|
| 1 | `fly/data/quotation.pyc` | 153/153 | 182759 | SAME |
| 2 | `fly/data/quote.pyc` | 91/92 | 94155 | SAME |
| 3 | `IQCommon/api/klinedata.pyc` | 64/64 | 102772 | SAME |
| 4 | `IQCommon/logger/handlers.pyc` | 29/30 | 9068 | SAME |
| 5 | `IQCommon/strategy/wizard_quant_api.pyc` | 58/58 | 34541 | SAME |
| 6 | `IQCommon/util/trade_info_utils.pyc` | 40/41 | 61379 | SAME |
| 7 | `IQData/api/api_base.pyc` | 28/28 | 33123 | SAME |
| 8 | `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 45/45 | 53841 | SAME |
| 9 | `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 27/27 | 13021 | SAME |
| 10 | `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 37/37 | 34308 | SAME |
| 11 | `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 121/128 | 178207 | SAME |
| 12 | `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 17/17 | 13299 | SAME |
| 13 | `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | 20555 | SAME |
| 14 | `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 43/43 | 55531 | SAME |
| 15 | `IQCommon/arg_checker.pyc` | **49/49** | 14924 | SAME |
| 16 | `IQData/utils/arg_checker.pyc` | **39/39** | 13410 | SAME |
| 17 | `IQEngine/utils/arg_checker.pyc` | **43/43** | 14822 | SAME |
| 18 | `IQCommon/profiler_func.pyc` | **17/17** | 8580 | SAME |
| 19 | `IQData/utils/profiler_func.pyc` | **15/15** | 5671 | SAME |
| 20 | `IQEngine/utils/profiler_func.pyc` | **18/18** | 9237 | SAME |

Rows 15–20 are the six duplicated-module canaries added after gate 31 attempt 1: all six are fully green
today, none is in the residual roster, and none was in the old 14-file panel — which is precisely why that
panel read clean on a merge that the gate measured at −6 units and −4 files. Any candidate that changes one
of these six counts is a regression, whatever its own victim does.
