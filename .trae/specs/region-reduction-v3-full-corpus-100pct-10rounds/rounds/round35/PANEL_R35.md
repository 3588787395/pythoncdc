# PANEL_R35 — 20-file panel for the R21-27 candidate `87910190b7ef7c35`

Rig `python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r30chk r35panel 0 20` (regen with the mirror's installed
sources, byte-cmp against the repo's sealed products, per-file units through
`scripts/pyc_verify.py single --source`). Base = gate-34 sealed, generator `065e4d77243190dc`.
Log: `D:/Temp/r35/panel_r35.log`, rc=0, `DONE`.

| file | sealed (gate 34) | under the candidate |
|---|---|---|
| `fly/data/quotation.pyc` | 153/153 | SAME 153/153 |
| `fly/data/quote.pyc` | 91/92 | SAME 91/92 |
| `IQCommon/api/klinedata.pyc` | 64/64 | SAME 64/64 |
| `IQCommon/logger/handlers.pyc` | 30/30 | SAME 30/30 |
| `IQCommon/strategy/wizard_quant_api.pyc` | 58/58 | SAME 58/58 |
| `IQCommon/util/trade_info_utils.pyc` | 41/41 | SAME 41/41 |
| `IQData/api/api_base.pyc` | 28/28 | SAME 28/28 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 45/45 | SAME 45/45 |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 27/27 | SAME 27/27 |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 37/37 | SAME 37/37 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 123/128 | **CHANGED 124/128** |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 17/17 | SAME 17/17 |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | SAME 12/13 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 43/43 | SAME 43/43 |
| canaries `arg_checker`×3 | 49/39/43 | SAME 49/39/43 |
| canaries `profiler_func`×3 | 17/15/18 | SAME 17/15/18 |

Exactly one product moved on the panel and it moved **up**; 19 of 20 files are byte-identical to the sealed
products, so unlike gate 31 attempt 1 and this round's own v1 candidate, nothing over-fires into a green
file. The census population behind the chain-wrap rule (`_r27_pairs > 1`) is 3 sites —
`etf_purchase_redemption`, `_process_order`, `get_covered_amount` — and `get_covered_amount` is re-measured
in-file as `delta=0 hunks=0 landings=0 judge_diff=False`, i.e. the one green site in that population is
untouched.
