# Fresh 全量基线（本规范唯一 before）

封表时点：2026-10-05（Task 1 执行时刻）
判据唯一：`scripts/pyc_verify.py`（ruler `pylingual/equivalence_check.py` sha256[:16] = `9c7567bd6776b36b`）
解释器：Python 3.11.7（`D:\Python\python.exe`）
工作树：`D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`，分支 `rr-v3r01-f557fd`
代码起点：merge commit `47785867` = `bcd55638`(rr-v3r00) + `main`(088b0579 ⊃ d8db3448 create_user_code_iqe 回退修复)
（主代理裁定：基线建在当前最好的代码上，已知回退不在本轮重查一遍）

## 一、读数总表

| 验证面 | 读数 | 与归档 round2 after 的位移 |
|--------|------|---------------------------|
| 402 全量（8 分片 batch 聚合） | units **6554/6617**（99.0479%）、files **369/402** success、failure 33、compile_error 0、error 0 | 逐文件 units 位移 = **0** |
| 34 小测试集（A+B1+B2 三片） | units **1505/1568**（A 473/515 + B1 513/528 + B2 519/525） | 持平（归档 1505/1568） |
| `fly/data/quotation.pyc` | **152/153**，唯一失败单元 `<module>.change_his_to_forward: Different control flow` | 同单元同读数 |
| `IQCommon/util/trade_info_utils.pyc` | **36/41** | 证明 spec.md Why 的 35/41 是过期读数，本基线取 36/41 |
| tests 六套件 | 277 passed / 2 failed / 2 xpassed | 基线名单不变：`test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function` |

交叉核对（Task 1.4）：`trade_info_utils` batch=36/41 与 `single`=36/41 逐位相等；`quotation` batch=152/153 与 `single`=152/153 逐位相等。

## 二、执行明细（每片 ≤300s 合规）

- regen：先删 402 个 A 类 `*OK.py`（实测删除 402、缺产物 0），再逐片 `pycdc.py -o` 重生成。
  shard0..7 = 51/51、51/51、51/51、51/51、51/51、51/51、51/51、45/45 ok，failed 合计 **0**。
- batch（八分片，`driver.py verify N`）：35.4s / 20.5s / 13.0s / 20.2s / 22.6s / 24.0s / 32.6s / 47.6s，合计 215.9s，逐片 rc=0。
  报告：`baseline/shards/shard{0..7}_report.json`
- 34 小测试集：`driver.py verify all34` 在 290s 内部上限 **rc=TIMEOUT**（driver_log.txt 在案），
  按 v2 同款做法拆分合规重跑：`small34_a.json`(17) → 206.4s、`small34_b.json`(17) 再按单元权重对半
  `small34_b1.json`(12 文件/528 单元) → 87.9s、`small34_b2.json`(5 文件/525 单元) → 91.6s。
  报告：`baseline/shards/small34_report_a.json`、`small34_report_b1.json`、`small34_report_b2.json`
- tests 六套件分两批跑（1-3 套件 1.49s、4-6 套件 3.81s）。

## 三、基线前的两处工具纠正（非判据、非算法）

1. `driver.py` 的 `ROOT` 由「上溯四级」改为「上溯三级」：r00 版本把仓库根算到 `app/f557fd`，
   首次 `regen 0` 实测 0 ok / 51 failed，逐条 rc=2、`can't open file '...app\f557fd\pycdc.py'`。
   同处加 fatal 自检：`ROOT` 下无 `pycdc.py` 即退出，禁止静默跑空。
2. `baseline/shards/shard{0..7}.json` + `full_index.json` + `small34_index.json` 的 `path` 前缀
   由 `6f79dd` 重绑到 `f557fd`：纯文本替换，`rel`/顺序/`function_count`/`size` 逐字节不变，
   断言「替换次数 == 条目数」且每条 `path.endswith(rel)` 通过（402 条全等）。
   必要性：`pyc_verify.batch` 直接取 `entry['path']`（不存在即 fatal），`compare` 以绝对 pyc 路径为键，
   同一规范线内所有报告必须同前缀才可比。原 6f79dd 前缀版本可从 `bcd55638` 恢复。
3. 语料与 pylingual 判据均不在 git 内（`*.pyc` 被 .gitignore），已把 `F:/Downloads/pythoncdc-main/site-packages`
   的 1721 个 pyc 按相对路径镜像进本工作树（1 个 quotation.pyc 已跟踪，合计 1722），F: 侧未被写入任何文件。

## 四、语料普查（本基线时刻重算，反向夹钳）

`python -X utf8 tools/corpus_census.py` → `total=1722 A=402 B=1312 C=8 A_delta=0`，
`index_entries=402 products_ok=402/402 missing_pyc=0`。

与 r00 封表读数 `total=1721 / C=7` 相比 **+1 个 C 类**，A 类零位移（A_delta=0，402 口径未变）。
新增者已按类别登记并附字节级证据，见 `baseline/exclusion_evidence.md`：
`IQCommon/util/email_utils.py.pyc` —— 不是字节码，前 8 字节为 ASCII `# Source`（Decompyle++ 生成的 py 文本被误命名为 .pyc），
magic `2320536f` ≠ cpython-3.11 的 `a70d0d0a`，marshal 失败。

## 五、残余缺口（本基线的 after 目标面，共 33 文件 / 63 单元）

单单元损失 23 个（Round 1 面，quotation 除外即 tasks.md 的 22 个）；
双单元 4 个（Round 2）、三单元 3 个（Round 3）、quotation 终局单元（Round 4）、
Different bytecode 残余（Round 5）、trade_live_broker 大损失（Round 6）。

| 文件 | units | 损失 |
|------|-------|------|
| IQCommon/data/finance.pyc | 31/32 | -1 |
| IQCommon/logger/handlers.pyc | 29/30 | -1 |
| IQCommon/util/cgroup_utils.pyc | 7/8 | -1 |
| IQCommon/util/email_utils.pyc | 3/4 | -1 |
| IQData/api/api_base.pyc | 27/28 | -1 |
| IQData/plugins/plugin_system_fly_basicdata/calexrights_func.pyc | 7/8 | -1 |
| IQData/utils/calexrights_func.pyc | 7/8 | -1 |
| IQEngine/core/bar.pyc | 84/85 | -1 |
| IQEngine/core/executor.pyc | 9/10 | -1 |
| IQEngine/core/strategy/strategy_universe.pyc | 10/11 | -1 |
| IQEngine/data/trading_dates_mixin.pyc | 13/14 | -1 |
| IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc | 18/19 | -1 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 26/27 | -1 |
| IQEngine/plugins/plugin_system_accounts/position_model/stock_position.pyc | 36/37 | -1 |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc | 12/13 | -1 |
| IQEngine/plugins/plugin_system_matcher/matcher.pyc | 16/17 | -1 |
| IQEngine/plugins/plugin_system_trade/function.pyc | 70/71 | -1 |
| IQEngine/utils/profiler_func.pyc | 17/18 | -1 |
| fly/common/flytools.pyc | 65/66 | -1 |
| fly/data/quotation.pyc | 152/153 | -1 |
| fly/data/quote_handler.pyc | 78/79 | -1 |
| fly/dumpload/load_daily.pyc | 26/27 | -1 |
| fly/logger.pyc | 63/64 | -1 |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | 43/45 | -2 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | -2 |
| fly/common/future_contract_info.pyc | 27/29 | -2 |
| fly/simtradding/ptradeAccount.pyc | 135/137 | -2 |
| IQCommon/api/klinedata.pyc | 61/64 | -3 |
| IQCommon/strategy/wizard_quant_api.pyc | 55/58 | -3 |
| IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc | 34/37 | -3 |
| IQCommon/util/trade_info_utils.pyc | 36/41 | -5 |
| fly/data/quote.pyc | 84/92 | -8 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | -10 |

## 六、v2 读数在本规范中的作废声明

`adversarial-complete-forms-v2-10rounds/rounds/round2/*_report_new.json` 与 Round 2 报告中
`trade_info_utils = 35/41` 的读数，属 P3 在途代码中间态，**自本文件起不得作为任何轮的 before**；
本规范全部 compare 的 before = 本文件的 `baseline/shards/*_report.json`。
v2 报告仅作为历史证据保留在原目录（本基线已用其做逐文件位移核对，结果 0 位移）。
