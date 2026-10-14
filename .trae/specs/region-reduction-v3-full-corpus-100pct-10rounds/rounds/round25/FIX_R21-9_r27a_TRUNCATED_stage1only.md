# FIX_R21-9 — engineer r27a — mechanism: arm statements emitted into a later suite

Owner file: `core/cfg/region_ast_generator.py` (repo READ-ONLY for me).
Branch `rr-v3r01-f557fd`, HEAD `705ce10d`.
Mirror: `D:/Temp/r27a/wt` · pristine: `D:/Temp/r27a/pristine` · products: `D:/Temp/r27a/out`

## Sections
1. Mirror build proof
2. Stage 1 baseline (unpatched mirror)
3. Exemplar A / B reproduction
4. 判据实现 (exact file:line + predicate)
5. Stage readings (panel + batteries)
6. 负面证据
7. Final declaration

STATUS: IN PROGRESS

## 1. Mirror build proof

Built `D:/Temp/r27a/wt` from repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
@ HEAD `705ce10d` (branch `rr-v3r01-f557fd`).

```
cp -r pycdc.py core parsers utils bytecode scripts /d/Temp/r27a/wt/
S=.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds
cp --parents -r $S/round14/{repro,repro_arm,repro_ccneg} $S/round18/repro_retbreak \
              $S/round19/{repro_orderapi,repro_tail} /d/Temp/r27a/wt/
```
All six battery dirs verified present at identical relative depth (runners print
`ROOT=D:\Temp\r27a\wt`, i.e. their 7-dirname resolution lands on the mirror root).

sha256 first-16, mirror files (self-certified):

| file | sha16 | expected |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `5043790fbeaca162` | `5043790fbeaca162` MATCH |
| `core/cfg/region_analyzer.py` | `b7f3076323813787` | MATCH (read-only) |
| `core/cfg/comprehension_generator.py` | `7d8acab92ccc7782` | MATCH (read-only) |
| `core/cfg/ast_generator_v2.py` | `beeaf14435e22922` | MATCH (read-only) |

Pristine snapshot copied to `D:/Temp/r27a/pristine/core` (region_ast_generator.py
re-verified `5043790fbeaca162`). `D:/Temp/r25b` and `D:/Temp/r26a` NOT used.
Products: only `D:/Temp/r27a/out/**`. No `*OK.py` in the repo. No `git` writes.

## 2. Stage 1 baseline — UNPATCHED mirror, generated then judged with `--source`

Generator: `python -X utf8 pycdc.py --region <pyc> -o out/base/<name>_prod.py` (cwd = mirror).
Judge: `python -X utf8 scripts/pyc_verify.py single <pyc> --source <that fresh product>`.
Every product freshly written under `D:/Temp/r27a/out/base/` (removed before regen);
no in-place `*OK.py` was read. Tree = unpatched mirror.

| panel file | read | brief | |
|---|---|---|---|
| fly/data/quote.pyc | 89/92 | 89/92 | OK |
| .../trade_live_broker.pyc | 119/128 | 119/128 | OK |
| IQCommon/strategy/wizard_quant_api.pyc | 57/58 | 57/58 | OK |
| .../real_quote.pyc | 44/45 | 44/45 | OK |
| IQCommon/api/klinedata.pyc | 63/64 | 63/64 | OK |
| IQCommon/logger/handlers.pyc | 29/30 | 29/30 | OK |
| IQCommon/util/trade_info_utils.pyc | 38/41 | 38/41 | OK |
| IQData/api/api_base.pyc | 27/28 | 27/28 | OK |
| .../fly_data/strategy/strategy.pyc | 26/27 | 26/27 | OK |
| .../realtime_event_source.pyc | 12/13 | 12/13 | OK |
| .../plugin_system_risk_calculation/__init__.pyc | 42/43 | 42/43 | OK |
| fly/data/quotation.pyc (sentinel) | 153/153 | 153/153 | OK |
| plugin_system_matcher/matcher.pyc (sentinel) | 17/17 | 17/17 | OK |
| plugin_fly_data/fly_api/order_api.pyc (sentinel) | 37/37 | 37/37 | OK |

quote's three red units are exactly `<module>.Quote.check_frequency`,
`<module>.Quote.run_individual_transform`, `<module>.Quote.run_tick_socket`.

Note: the brief's order_api panel path `IQCommon/api/order_api.pyc` does not exist; the
real corpus file is `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` (memory
already flags "the corpus pyc paths my briefs kept getting wrong"). Same for matcher =
`IQEngine/plugins/plugin_system_matcher/matcher.pyc`.

Batteries, unpatched mirror:

| battery | read | recorded | |
|---|---|---|---|
| round14/repro | RED=9 / 9 | 9R/9 | OK |
| round14/repro_arm | GREEN=0 RED=3 / 3 | 0G/3R | OK |
| round14/repro_ccneg | GREEN=3 RED=1 / 4 | 3G/1R | OK |
| round18/repro_retbreak | GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4 | 2G/2R DRIFT=0 | OK |
| round19/repro_orderapi | GREEN=5 RED=0 / 5 | 5G/0R | OK |
| round19/repro_tail | GREEN=13 RED=0 / 13 | 13G/0R | OK |

MIRROR CERTIFIED — every value reproduces the brief.

