# Round 9 VERIFICATION（主代理自有复测封表）

封表时点：2026-10-08（判据唯一 `scripts/pyc_verify.py`，ruler `selfcheck` 于 `fly/data/quotation.pyc`
自证 153/153 Equal ∧ 常量变异抓到 ∧ 极性变异抓到 ＝ 判据可用；CPython 3.11.7 64 位）。

工单：`r9-fix-elif-chain-grouping`（第三攻，生成端）→ 落地 **B124 + B125**，
落地声明与判据见 `FIX_B124_B125_ELIFCHAIN.md`。
工程师在 150 回合上限处被截断且**未交回报告**（回报文件 0 字节），
故下列读数**全部由主代理自有命令重跑取得**，不采信其自述；其 scratch 留在
`D:/Temp/rrv9/`（`regress_step3.log`、`after2_targets.json` 等）作对照证据。

## 一、验证序六步（spec 次序，不可交换）

| # | 步骤 | 命令面 | 读数 | 判定 |
|---|---|---|---|---|
| 0 | 402 产物重生成 | `regen_list.py` 分 8 片，**每片先删后产** | `ok=51×7 + 45 = 402`，`bad=0`，单片 25–32s | ✓ |
| 1 | 34 小测试集 batch | `pyc_verify batch --index baseline/small34_index.json` | units **1526 → 1528**／1568，files success **16 → 18**，`REGRESSIONS=0 IMPROVED=2` | ✓ 零回退 |
| 2 | 402 八分片 batch + compare | `pyc_verify batch --index baseline/shards/shardN.json` → `rounds/round9/after/`；逐片 `compare --before round8 --after round9` | units **6575 → 6577**／6617（99.3653% → **99.3955%**），files **384 → 386**／402；八片 `REGRESSIONS=0`（0 片 778→779 IMPROVED=1；6 片 790→791 IMPROVED=1；其余不变） | ✓ **双门禁** |
| 3 | quotation 单验 | `pyc_verify single site-packages/fly/data/quotation.pyc` | `status=success units=153/153` | ✓ 零新增 |
| 4 | tests 六套件 | `pytest -q tests/test_algorithm_correctness.py test_deep_nesting_pressure.py test_control_flow_completeness_matrix.py test_complete_syntax_coverage.py test_boundary_cases.py test_core_functional.py` | **2 failed / 277 passed / 2 xpassed**，失败恰为基线那二条（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`） | ✓ 零新增失败 |
| 5 | IV.2 门禁自检 | 见下 §三 | 全项通过，两项如实登记为缺口 | ✓（带登记） |
| 6 | 读数汇报 | 本文件 §二/§四 | — | ✓ |

## 二、逐单元面（门禁的真正凭据，不是总数）

`rounds/round8/after` 与 `rounds/round9/after` 的 rows 逐文件对齐（402 文件集合相等，已 assert）：

- **UNIT_REGRESSIONS = 0**（无任何文件 `units_success` 下降）；
- **新增失败单元 = 0**（失败单元名集差集为空）；
- 翻正单元 2 条，**两条都在 §X「只差 1 单元」名单上**，与预测完全吻合：
  - `IQCommon/data/finance.pyc :: <module>.get_fields` → 31/32 → **32/32 success**
  - `IQEngine/plugins/plugin_system_trade/function.pyc :: <module>.reconnect` → 70/71 → **71/71 success**
- 「≥1 个 pyc 由 failure 转 success（同目录 `+OK.py` 全单元 Equal）」＝**达成 2 个**。

## 三、IV.2 自检逐条

| 项 | 读数 |
|---|---|
| IMPORT_OK / COMPILE_OK | `py_compile` 通过；`ast.parse`（`utf-8-sig`）通过 |
| BOM 单头 | `efbbbf` 恰 1 个，位于文件首 |
| CRLF 原样 | 未被整文件改写：改动行 194 行 vs 全文 CRLF 行 59,107（若换行被归一会显示数万行改动） |
| 无遗留插桩 | 新增行内 `print(` 命中 **0**；`TODO/FIXME/XXX_DEBUG` **0** |
| G3 前缀 | `def _?(fix|merge|patch|fallback|hack|workaround|temp)_` 命中 **0**；新方法仅 `_split_arm_at_chain_exit` |
| G4 特判 | 按文件名/函数名、绝对偏移阈值、长度计数的门控正则命中 **0** |
| 影响面抽验 | 逐单元差集只有上述 2 条变化；哨兵锚集（`quotation/flytools/history_data_source/quote_handler/ptradeAccount`）454/454 保持（工程师跑过、主代理另以 §一.3 单验 quotation） |
| 尺子自检 | `selfcheck quotation.pyc` ＝ 自证 153/153 ∧ 两变异各抓到 ＝ OK。 |

**登记项 1（仪器用法）**：`selfcheck` 必须选**全 Equal 的文件**。首轮我拿
`trade_info_utils.pyc` 跑，得「自证 37/41 … 自证失败」——那是该文件本身有 4 个失败单元，
不是尺子坏；已改用 `quotation.pyc` 复跑并以此数入账。
**登记项 2（本票牙缺）**：工程师**未建 ≥10 条最小复现臂**（`test_repros/round9/` 内
`b124/b125/elifchain/chainexit` 命名臂命中 0）。本票是按**逐单元翻转**接受，
补臂已登记为轮 10 前置项（见 `FIX_B124_B125_ELIFCHAIN.md` §四.1 与 tasks.md 10.0）。

## 四、封表残余（40 单元 / 16 文件，未改判据、未凑读数、未删语料）

| 文件 | units | 失败单元数 |
|---|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | 10 |
| `fly/data/quote.pyc` | 86/92 | 6 |
| `IQCommon/util/trade_info_utils.pyc` | 37/41 | 4 |
| `IQCommon/api/klinedata.pyc` | 61/64 | 3 |
| `IQCommon/strategy/wizard_quant_api.pyc` | 55/58 | 3 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 43/45 | 2 |
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | 35/37 | 2 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 41/43 | 2 |
| `IQCommon/logger/handlers.pyc` | 29/30 | 1 |
| `IQData/api/api_base.pyc` | 27/28 | 1 |
| `IQEngine/core/bar.pyc` | 84/85 | 1 |
| `IQEngine/core/strategy/strategy_universe.pyc` | 10/11 | 1 |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 26/27 | 1 |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | 1 |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 16/17 | 1 |
| `fly/dumpload/load_daily.pyc` | 26/27 | 1 |

⇒ 距 100% 还差 **40 单元 / 16 文件**；「只差 1 单元即可整文件 OK」的文件由 10 个降为 **8 个**
（`finance`、`function` 已出列）。残余按 §XVI 的分派继续走 #16 → #14 → #13 → #15 队列；
`#18` 已作为假轴撤销。

## 五、本轮结论

Round 9 门禁**达标**（≥1 pyc 转 success 实为 2 个，`REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0`，
quotation 与六套件零新增），可提交并 push。**未达 100%**：残余 40 单元如实上表，
判据未改、产物未手改、语料未删。
