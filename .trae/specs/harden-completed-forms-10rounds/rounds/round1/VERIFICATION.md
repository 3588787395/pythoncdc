# Round 1 主代理验证读数（VERIFICATION）

验证人：主代理（唯一判据 = `scripts/pyc_verify.py`，全部命令 ≤300s，402 全量 = 8 分片重生成 OK.py + batch + compare）

## 全量 402（当前树 vs 基线 a9ac63e3）

| 指标 | 基线 | 本轮 | 变化 |
|---|---|---|---|
| 单元级 success | 6546/6617（98.93%） | **6554/6617（99.05%）** | **+8** |
| 文件级 success | 368/402 | **369/402** | +1（jq_trans_module failure→success） |
| Movement Matrix | — | **REGRESSIONS=0**（文件级+单元级双查） | IMPROVED=1 |
| 反编译错误/编译错误 | 0/0 | 0/0 | — |

单元级差异明细（仅改善，无回落）：
- `IQCommon/strategy/jq_trans_module.pyc` 63→65（B1b 嫁接落地）
- `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` 115→118
- `fly/data/quote.pyc` 81→84

## 回退拦截记录（R1.4c）

首轮 sweep 发现 1 单元回落：`plugin_system_risk_calculation/__init__.pyc get_daily_summary` 41→40（Different bytecode）。打回修复工程师三：根因 = **c53df077 在途变更 R76-A1/A2 的 MERGEPATH 前导守卫剥离**误触发（非 B1b/B6），修复 = MERGEPATH 剥离点加 [R1-REG 守卫·R59-B 升级消费端让位]（行为探针双校验，结构判据，见 FIX_REG.md）。复验后 8 片全部重跑：**回退归零**（risk_calculation 41/43，剩余 2 失败 = 基线既有），shard5 回到 993/999。

## quotation.pyc

`site-packages/fly/data/quotation.pyc`：**152/153（99.35%）**，唯一失败 `change_his_to_forward` = 基线既有，零新增失败。

## 现有区域相关测试（tests/）

| 测试文件 | 读数 |
|---|---|
| test_complete_syntax_coverage | 80 passed |
| test_control_flow_completeness_matrix | 94 passed |
| test_ternary_combinations | 27 passed + 3 xpassed |
| test_algorithm_correctness | 19 passed + 1 failed（B01_simple_if_then_else_merge） |
| test_deep_nesting_pressure | 14 passed + 1 failed（BOUNDARY_02_large_function） |
| test_boundary_cases | 22 passed + 1 failed（BND_21_walrus）+ 2 xpassed |

3 个失败用例经基线（a9ac63e3，git archive 隔离环境复跑）确证**基线既有**，本轮**零新增测试失败**。

## 小测试集（34 pyc，baseline/failing_index.json 逐文件对照）

**worse = 0**；improved = 3（quote 81→84、trade_live_broker 115→118、jq_trans_module 63→65），其余持平。

## 轮门禁判定

- ≥1 破口封闭：**达成**（B1b 封闭 + B6 浅层封闭 + 在途变更 R1-REG 守卫补全过审）
- ≥1 pyc 读数改善：**达成**（jq_trans_module 文件级 success，3 文件单元级 +8）
- 无回退：**达成**（文件级/单元级/测试套件三层零回退）
- 遗留交接：B7（外层循环包裹混合链降级，基线既有，交 Round 2）；B5 候选（未分离独立失败，不盲目修）；FSTRINGPATH 站点未镜像让位守卫（无升级端竞争，观察项）

## 工具与产物

- 验证驱动：`rounds/round1/verify_driver.py`（regen/verify/compare 三模式，402 重生成全部成功 0 失败）
- 分片新报告：`rounds/round1/shard0..7_report_new.json`；基线分片：`baseline/shards/`（自 a9ac63e3 提取）
- 评审：`REVIEW.md`（首轮攻击 14 MISMATCH/11 MATCH）、`REVIEW2.md`（复核放行 + B7 登记 + rv_01..10 探针）
- 修复：`FIX.md`（B1b 五臂）、`FIX_B6.md`（B6 七处）、`FIX_REG.md`（R1-REG 守卫）
