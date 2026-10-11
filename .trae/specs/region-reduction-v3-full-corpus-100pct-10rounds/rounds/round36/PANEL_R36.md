# PANEL_R36 — 20-file pre-gate panel for hunk A (R21-33a), generator `87910190b7ef7c35` → `7344dcc566442e58`

Rig `python -X utf8 D:/Temp/t30/panel14.py D:/Temp/r30chk r36full 0 20`; raw log
`D:/Temp/t30/log_panel_r36full.txt`. Regenerates each panel pyc with the mirror's installed
sources, byte-compares against the sealed product, then reads per-file units from a fresh
`pyc_verify single --source`.

| file | bytes | vs sealed | units |
|---|---|---|---|
| fly/data/quotation.pyc | 182759 | SAME | 153/153 |
| fly/data/quote.pyc | 94155 | SAME | 91/92 |
| IQCommon/api/klinedata.pyc | 102772 | SAME | 64/64 |
| IQCommon/logger/handlers.pyc | 9030 | SAME | 30/30 |
| IQCommon/strategy/wizard_quant_api.pyc | 34541 | SAME | 58/58 |
| IQCommon/util/trade_info_utils.pyc | 61343 | SAME | 41/41 |
| IQData/api/api_base.pyc | 33123 | SAME | 28/28 |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | 53841 | SAME | 45/45 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 13021 | SAME | 27/27 |
| IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc | 34308 | SAME | 37/37 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 178495 | **CHANGED** | 124/128 (held) |
| IQEngine/plugins/plugin_system_matcher/matcher.pyc | 13299 | SAME | 17/17 |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | 20555 | SAME | 12/13 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 55531 | SAME | 43/43 |
| IQCommon/arg_checker.pyc (canary) | 14924 | SAME | 49/49 |
| IQData/utils/arg_checker.pyc (canary) | 13410 | SAME | 39/39 |
| IQEngine/utils/arg_checker.pyc (canary) | 14822 | SAME | 43/43 |
| IQCommon/profiler_func.pyc (canary) | 8580 | SAME | 17/17 |
| IQData/utils/profiler_func.pyc (canary) | 5671 | SAME | 15/15 |
| IQEngine/utils/profiler_func.pyc (canary) | 9237 | SAME | 18/18 |

Decreases: **0**. Files whose bytes moved: **1** (broker). The whole corpus-visible effect of the
rule on this panel is one added line in the broker product:

```
+        self.trade_info = get_trade_status(self.trade_id, return_trade_info=True)
```

at `trade_live_brokerOK.py:899`, inside `_trade_status_handle`, and the victim unit's `del=9` hunk
`@46..@90` disappears (`delta=-3 hunks=3` → `delta=+6 hunks=2`, `landings` unchanged). No file
flips on the panel, so the panel alone cannot decide the ticket: the rule is a general
statement-boundary rule and must be judged on all 402 verification-face files, which is gate 36.

## Companion measurements on the same base (not installed)

| candidate | base → build | victim unit | file units |
|---|---|---|---|
| R21-33a (hunk A, generator) | `87910190b7ef7c35` → `7344dcc566442e58` | `_trade_status_handle` −3/3 → **+6/2** | broker 124/128 |
| R21-33b (hunk B, analyzer) | `35e227ac3e7b25af` → `efd455859b69d8a1` | −3/3 → **+1/2** | broker 124/128 |
| R21-33c (hunk C, generator, paired with B) | `87910190b7ef7c35` → `7a02cc2a06d55447` | −3/3 → **−85/2** (regression) | broker 124/128 |
| M1+M3b merged (generator) | `87910190b7ef7c35` → `3d4f27de6d80ab6e` | `clock_worker` −113/7 → **−3/8** | realtime_event_source 12/13 |
