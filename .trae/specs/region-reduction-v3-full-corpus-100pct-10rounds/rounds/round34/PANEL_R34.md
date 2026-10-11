# PANEL_R34 — 20-file panel readings for the R21-28 candidates

Rig `python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r30chk <tag> 0 20` (regen with the mirror's installed
sources, byte-cmp against the repo's sealed products, then per-file units through
`scripts/pyc_verify.py single --source`). Base = gate-33 sealed, generator `fcf2b870f0fb71b3`.
Logs: `D:/Temp/r34/panel_r34p.log` (v1), `D:/Temp/r34/panel_r34v2.log` (v2).

| panel file | sealed (gate 33) | v1 `724f1843f9522fec` (interior only) | v2 `065e4d77243190dc` (3 conjuncts) |
|---|---|---|---|
| `fly/data/quotation.pyc` | 153/153 | SAME 153/153 | SAME 153/153 |
| `fly/data/quote.pyc` | 91/92 | CHANGED **90/92** ← regression | SAME 91/92 |
| `IQCommon/api/klinedata.pyc` | 64/64 | SAME 64/64 | SAME 64/64 |
| `IQCommon/logger/handlers.pyc` | 30/30 | SAME 30/30 | SAME 30/30 |
| `IQCommon/strategy/wizard_quant_api.pyc` | 58/58 | SAME 58/58 | SAME 58/58 |
| `IQCommon/util/trade_info_utils.pyc` | 41/41 | CHANGED 41/41 | CHANGED 41/41 (bytes move, units hold) |
| `IQData/api/api_base.pyc` | 28/28 | SAME 28/28 | SAME 28/28 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 45/45 | CHANGED **44/45** ← regression | SAME 45/45 |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 27/27 | SAME 27/27 | SAME 27/27 |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 37/37 | SAME 37/37 | SAME 37/37 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 122/128 | CHANGED **123/128** ← flip | CHANGED **123/128** ← flip |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 17/17 | SAME 17/17 | SAME 17/17 |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | SAME 12/13 | SAME 12/13 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 43/43 | SAME 43/43 | SAME 43/43 |
| `IQCommon/arg_checker.pyc` (canary) | 49/49 | SAME 49/49 | SAME 49/49 |
| `IQData/utils/arg_checker.pyc` (canary) | 39/39 | SAME 39/39 | SAME 39/39 |
| `IQEngine/utils/arg_checker.pyc` (canary) | 43/43 | SAME 43/43 | SAME 43/43 |
| `IQCommon/profiler_func.pyc` (canary) | 17/17 | SAME 17/17 | SAME 17/17 |
| `IQData/utils/profiler_func.pyc` (canary) | 15/15 | SAME 15/15 | SAME 15/15 |
| `IQEngine/utils/profiler_func.pyc` (canary) | 18/18 | SAME 18/18 | SAME 18/18 |
| **net on the panel** | | **+1 −1 −1 = −1 unit** ⇒ rejected | **+1 unit, no file down** ⇒ goes to the gate |

## Unit shapes of the six broker residuals, under v2

Measured with `unit_diff.py … --prod D:/Temp/t30/out/r34v2_…trade_live_broker.py`:

| unit | sealed base | under v2 |
|---|---|---|
| `ipo_stocks_order` | −1 / 1 hunk / 1 landing, judge_diff=True | **0 / 0 / 0, judge_diff=False** |
| `_process_order` | −465 / 4 / 1 | −465 / 4 / 1 (unchanged) |
| `_process_cancel_order` | −293 / 3 / 0 | −293 / 3 / 0 (unchanged) |
| `_sync_worker` | −3 / 5 / 6 | −3 / 5 / 6 (unchanged) |
| `_trade_status_handle` | −3 / 3 / 2 | −3 / 3 / 2 (unchanged) |
| `etf_purchase_redemption` | −12 / 5 / 0 | −12 / 5 / 0 (unchanged) |

## What v1's damage looked like, and what v2 changed

v1 emitted two `continue` lines into `trade_live_brokerOK.py`: the victim's (line 2332, inside the
`if stock_type == 'Y':` arm) and a byte-neutral one in the green unit `get_margin_contractreal`
(line 1978). In `quote.pyc` / `real_quote.pyc` it emitted a `continue` inside
`one_prod_to_dataframe`'s arm, whose block **carries statements** (`index.append(temp_time)` before the
back-edge); the added `continue` made the 14 instructions that follow it unreachable, and CPython's
dead-code elimination removed them (`518 -> 504` measured on the compiled unit), which is what the judge
then failed. v2's statement-payload conjunct refuses exactly that class of block, and the two files came
back to byte-identical products.

`trade_info_utils.pyc` still changes bytes under v2 (six of its blocks qualify by the census) while
staying 41/41: the inserted continues compile to the same instruction stream, so the units hold. Recorded
here rather than glossed over, because a product that moves without a unit change is the shape that
later turns into a regression if the criterion is widened again.
