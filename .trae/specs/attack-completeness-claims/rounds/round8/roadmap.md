# roadmap — 完备方法落地路线图（Task 8.3 / Task 9 承接）

> 目标：把 `COMPLETENESS_METHOD.md` v3 的四支柱与 G1–G6 变成可执行工具、可复算证据和可阻断发布的门禁。
> 预算：初始估算 **32 工程日**（4+6+5+7+6+4），由变更控制调整；降低预算不得降低 G1–G6 口径。
> 当前状态：**S0 设计完成（待复审）**，S1–S6 均未开始；G5 回归绿，G1–G4/G6 未达成或不可评。
> 纪律：不改 `tests/`；不动 402 认证产物；不按语料特判；不缩小 J 分母；不删除失败证据。

---

## §0 角色与交付边界

| 角色 | 职责 | 不承担 |
|---|---|---|
| A 规范/评审负责人 | 维护 J schema、门槛口径、破口映射、验收签收 | 不实现产品规则 |
| B 工具实现者 | 实现 `tools/completeness/*`、runner、报告生成 | 不自签「完备」 |
| C 独立红队/审计 | canary 保管、复审、泄漏扫描、证据抽查 | 不参与被审工具实现 |
| D CI/发布 | 接入门禁、归档证据、阻断发布 | 不改判据口径 |

**Task 9 只做工具与门禁，不修 B142/B143/B172–B178 等产品缺陷；缺陷修复归 Task 10。**

---

## §1 阶段总览

| 阶段 | 交付 | 依赖 | 预算 | 门槛贡献 |
|---|---|---|---|---|
| S0 | `COMPLETENESS_METHOD.md` v3 + `METHOD_REVIEW.md` + 本路线图 | — | 已完成（第三轮有条件通过，2 项已修） | 口径 |
| S1 | J schema 固化 + `jspace_generator.py` + 五元组 `coverage_checker.py` | S0 | 4 日 | G1 |
| S2 | `semantic_diff.py` MVP（R1–R5/R7） | S1 | 6 日 | G2a/G2b/G2c |
| S3 | `mutation_test.py` + 等价变异体证明 | S2 | 5 日 | G3 |
| S4 | `rule_manifest.json` + 独立规则全集 + 锚点对账 + 覆盖引理 | S1 + S2 | 7 日 | G4 |
| S5 | `fuzz_driver.py` + 最小化 + 24 canary | S2 | 6 日 | G6 |
| S6 | CI/E 门禁 + 双读数台账 + 独立审计 | S1–S5 | 4 日 | G1–G6 汇总 |

### Task 9 子项映射

| Task 9 | 覆盖阶段 | 交付 |
|---|---|---|
| 9.1 | S2 | `semantic_diff.py`（R1–R5/R7、签名绑定、`body_reached`） |
| 9.2 | S3 | `mutation_test.py`（独立变异总体、等价证明、漏检/误杀） |
| 9.3 | S1 | `jspace_generator.py` + 五元组 `coverage_checker.py` |
| 9.4 | S4 | `rule_manifest.json` + 独立规则全集 + 双向对账 |
| 9.5 | S5 | `fuzz_driver.py` + 最小化 + 24 canary |
| 9.6 | S6 | G1–G6 门禁 + 双读数 + 独立审计 + 原有回归 |
| 9.7 | — | 提交并 push `rr-v4r09:` |

---

## §2 S1 — 判定空间与五元组覆盖（G1）

### 交付

- `tools/completeness/jspace_generator.py`：J v1 唯一生成源；固定 seed；输出 `judgment_space.json`、`P_j`、`expected_label`、`input_model`、`entrypoint`、`host_prelude`、`counterexample_hint`、`excluded[]`。
- `tools/completeness/coverage_checker.py` 升级：C1–C5 五元组；输出 `J_total, covered_5tuple, probe_only, unexecuted, n/a, inconclusive, excluded, uncovered[], checker_version`。
- `logs/jspace_manifest.json`、`logs/coverage_report.json`、`logs/excluded_audit.md`。

### 验收读数

- `J_total = 1556`（v1 分母不变）；生成器重复运行字节级一致；
- 检查器用合成正例/反例自测通过：缺 C1/C2/C3/C4/C5 各至少 1 例均判未覆盖；
- 旧 `976/1556` 只出现在 `probe_only`，不得出现在 `covered_5tuple`；
- `excluded[]` 每条有语言理由；`arg/arguments`、签名、docstring 有归属（J 或 R7）；
- J 充分性由 C 角色独立审查，A 签收。

### 命令（占位，实现后固化）

```
python tools/completeness/jspace_generator.py --check --json logs/jspace_manifest.json
python tools/completeness/coverage_checker.py --j judgment_space.json --evidence . --json logs/coverage_report.json
```

### 回退

- 生成器不可复现 → 冻结 J v1，保留现有清单，禁止手工补条目；G1 记 `INCONCLUSIVE`。
- 检查器不能区分五元组 → 停止 S2，先修检查器；不得用 probe-only 继续。

---

## §3 S2 — 语义差分 MVP（G2a/G2b/G2c）

### 交付

- `tools/completeness/semantic_diff.py`：`SourcelessFileLoader` 加载原 pyc；产物 `*OK.py` 导入；子进程沙箱；R1–R5、R7；`semantic_case` schema；`EQUAL/DIFF/INCONCLUSIVE/ERROR`。
- `tools/completeness/semantic_runner.py`（可选）：J/402/真实项目分片执行。
- `logs/semantic_diff_j.jsonl`、`logs/semantic_diff_402.jsonl`、`logs/semantic_diff_real.jsonl`、`logs/semantic_diff_digest.md`。

### 验收读数

- 100 条 J 用例：`DIFF=0`、`INCONCLUSIVE=0`、`N/A=0`；
- 至少 20 个已知错误变异/已知 DIFF 样本被判 `DIFF`（证明非空真）；
- 至少 5 个超时/不可导入样本被判 `INCONCLUSIVE`/`PRODUCT_ERROR`，不得判绿；
- 402：每个 artifact 至少 1 个 import case；可建模 code object 列表与 N/A 列表公开；
- 真实项目：46 个 pyc 全跑；7/46 不可编译必须计入 `DIFF/PRODUCT_ERROR`；`except*` 真实样本缺口保留；
- R7 对 docstring/annotations/signature/defaults/装饰器顺序/别名图有正反例自测。

### 命令（占位）

```
python tools/completeness/semantic_diff.py --case-file logs/j_cases.jsonl --json logs/semantic_diff_j.jsonl
python tools/completeness/semantic_diff.py --artifacts 402 --json logs/semantic_diff_402.jsonl
python tools/completeness/semantic_diff.py --real offcorpus --json logs/semantic_diff_real.jsonl
```

### 回退

- 沙箱不稳定 → 缩小到纯函数/固定输入，未覆盖条目记 `N/A`，G2 不得通过；不得把 `N/A` 算绿。
- 产物不可编译 → 记 `PRODUCT_ERROR`，修产品归 Task 10；不得跳过。
- R7 的身份比较引入误报 → 改为身份图同构 + 声明规范化，保留原始证据。

---

## §4 S3 — 变异测试（G3）

### 交付

- `tools/completeness/mutation_test.py`：≥12 类变异（值/分支/删除/换序/别名/转义/注解/docstring/装饰器顺序/异常别名/循环控制/局部-属性/类属性/边界）。
- `logs/mutation_report.json`：`killed, survived, equivalent, invalid, false_kill`。
- `logs/equivalent_proofs/`：等价变异体的机器可检证明或排除理由。

### 验收读数

- 集合互斥：`N = killed + survived`，`accepted = killed + survived + E`，`E = false_kill + true_neg`；`killed` 与 `false_kill` 不重叠；
- `survived=0` 且 `false_kill=0` 才可 G3；`miss_rate = survived / N`、`false_kill_rate = false_kill / E` 公开；
- 校准集：≥50 个已知坏变异全部 `killed`；≥20 个已知等价变异 `false_kill=0`；
- 每个 `survived` 登记为判据盲区/产品缺陷；不得从分母删除；
- `equivalent` 无证明 → 归入 `N`，按 oracle 结果进 `killed` 或 `survived`；证明不可复算 → 不计 `E`；
- 报告 `invalid/M_total`；若 >30%，G3 记 `INCONCLUSIVE`，先修变异生成器；
- 旧 `366/1311=27.92%` 只作为历史结构读数，不进入 G3。

### 命令（占位）

```
python tools/completeness/mutation_test.py --cases logs/j_cases.jsonl --oracle semantic_diff --json logs/mutation_report.json
```

### 回退

- 误杀率高 → 先修 harness/R7 规范化，不修判据口径；
- 等价证明不可机检 → 全部按 `survived` 计，G3 不通过；
- 变异体不可编译 → 记 `invalid`，不记 `killed`。

---

## §5 S4 — 规则清单与覆盖引理（G4）

### 交付

- `tools/completeness/rule_manifest.json`：`rule_id/anchor/pattern/preconditions/effect/guards/invariants/semantic_domain/witnesses/composition/proof/status`。
- **独立规则全集枚举器**：从 `core/cfg/**` 的规则分派分支/区域类型/生成器入口静态枚举 `rule_universe`；`total_rules = |rule_universe|`，不由 manifest 的 canonical 正则定义。
- 锚点扫描器：canonical 正则只做映射 + `unmapped_anchors`/`orphan_rules` 对账。
- `logs/rule_coverage.json`、`logs/rule_universe.json`、`logs/rule_proofs/`、`logs/rule_counterexamples/`。

### 验收读数

- `total_rules = |rule_universe| > 0`；`unmapped_anchors=0`、`orphan_rules=0`；
- 每条规则至少 1 正例 + 1 反例；反例是同 `pattern` 最小编辑、改一个前置条件后不触发；
- `semantic_domain` 每个声明 `H×D` 单元至少 1 见证；
- 每个 guard 调用点至少 1 负例；`continue`/`break`/`finally` 守卫显式覆盖 loop/handler；
- 每条规则至少 1 个 O6 组合见证（D2 + 相邻规则）；
- `proved_rules = total_rules` 才可 G4；`0/0` 或独立枚举器失败记 `INCONCLUSIVE`；
- B172 三元组、B173/B174 双归属、B175 守卫闭包、B178/B183 计数口径进入 manifest 或强制 J 条目。

### 命令（占位）

```
python tools/completeness/rule_universe.py --code core/cfg --json logs/rule_universe.json
python tools/completeness/rule_manifest.py --check --universe logs/rule_universe.json --json logs/rule_coverage.json
python tools/completeness/coverage_checker.py --rules logs/rule_coverage.json --json logs/rule_gate.json
```

### 回退

- 规则无法映射 → 补 J 生成器/锚点扫描器，不改 J 分母；
- 证明不可复算 → 降级 `tested-only`，G4 不通过；
- 独立枚举器无法枚举 → G4 记 `INCONCLUSIVE`，不得退回 manifest 自证；
- 锚点口径冲突 → 以独立枚举结果为准，台账注明 191/174/123 差异。

---

## §6 S5 — Fuzz、最小化与金丝雀（G6）

### 交付

- `tools/completeness/fuzz_driver.py`：3.11 文法生成器、属性测试、差分执行、预算控制。
- `tools/completeness/minimize.py`：源码/AST ddmin；保留原始输入与 seed。
- `canary/`：24 条隐藏探针（3 类×8），C 角色保管；季度轮换；泄漏扫描。
- `logs/fuzz_report.jsonl`、`logs/minimized/`、`logs/canary_report.json`、`logs/canary_leak_scan.md`。

### 验收读数

- 周级 ≥4 CPU 小时；连续 4 小时无新 `DIFF` 才可停止本轮；
- 任何 `DIFF` 有最小复现 + seed + 原始输入；未最小化不得关闭；
- 24/24 canary `EQUAL`；泄漏扫描 0；轮换记录完整；
- 生成器不得 import 产品代码；与产品实现者分离；
- G6 在 runner 落地前记「未建立」，不得用文字代替。

### 命令（占位）

```
python tools/completeness/fuzz_driver.py --hours 4 --seed 0 --json logs/fuzz_report.jsonl
python tools/completeness/minimize.py --input logs/fuzz_report.jsonl --out logs/minimized/
python tools/completeness/canary_runner.py --canary canary/ --json logs/canary_report.json
```

### 回退

- 崩溃不可复现 → 保留原始输入/seed/环境，不删除；
- canary 泄漏 → 本轮证据作废，轮换后重跑；
- 预算不足 → 延长周级窗口，不降低 G6 的 24/24。

---

## §7 S6 — 门禁、双读数与独立审计

### 交付

- CI 接入：L-A 提交级、L-B 夜间、L-C 周级、L-D 发布级。
- `tools/completeness/gate_report.py`：G1–G6 + 旧 E 门禁汇总；双读数模板。
- `logs/gate_report.json`、`logs/dual_readings.md`、`logs/audit/`。
- v9 台账：B163–B219 + U-01–U-06 逐条状态、证据路径、签收人。

### 验收读数

- G5：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、tests 基线、IV.2 全绿；
- G1–G4/G6 按各自阶段读数；任一失败 → 发布阻断；
- 报告模板必须同时出现形态基线与判定空间；禁止单写 128/128 或 6617/6617；
- 独立审计抽查 ≥10% 证据，含至少 1 个失败/`N/A`/`INCONCLUSIVE` 记录；
- 结论只能是「形态基线达成」「J 门槛达标」「语料完备」之一，且附条件与日期；
- 未满足时不得写「完备」。

### 命令（占位）

```
python tools/completeness/gate_report.py --all --json logs/gate_report.json
python tools/completeness/dual_readings.py --gate logs/gate_report.json --out logs/dual_readings.md
```

### 回退

- 任一门槛失败 → 阻断发布，回退到上一绿基线；
- 审计发现证据不可重放 → 该读数降级为「观察」，重跑后再签收；
- 双读数缺失 → 整个报告无效，不得发布。

---

## §8 依赖、并行与里程碑

```
S0 ──> S1 ──> S2 ──> S3
        │      ├──> S5
        └──────┴──> S4
S1–S5 ─────────────> S6
```

- S1 与 S2 可部分并行（J schema 稳定后即可做 pyc loader）；S3/S5 依赖 S2 的 oracle；S4 依赖 S1 的 J 映射 + S2 的语义差分（O5），不能只依赖 S1；S6 最后汇总。
- 里程碑 M1（S1+S2）：能对 100 条 J 做真实语义差分，且不产生假绿。
- M2（S3+S4）：变异漏检与规则覆盖可量化，G3/G4 可评。
- M3（S5+S6）：canary、fuzz、门禁、双读数、审计闭环。

---

## §9 当前读数与发布判定

| 门槛 | 当前读数 | 判定 |
|---|---|---|
| G1 | 旧 976/1556 probe-only；五元组未实现 | 不可评 |
| G2a | 无 `semantic_diff` | 未建立 |
| G2b | 无 402 输入模型；旧 4/46 是结构判据 | 未建立 |
| G2c | 46 个真实 pyc 未做语义差分；7/46 不可编译；`except*` 0 | 未建立 |
| G3 | 旧 366/1311=27.92% 是结构判据 | 未建立 |
| G4 | 无独立规则全集、无 manifest；0/0 不可用 | 未建立 |
| G5 | 6617/6617、1568/1568、153/153 | 绿（仅回归） |
| G6 | 24 canary 未建立 | 未建立 |

**发布判定**：当前只能写「形态基线达成；J 门槛达标/语料完备未达成」。S1–S6 完成并按 G1–G6 复验前，禁止对外声称完备。

---

## §10 变更控制

- 任何 J 分母、G1–G6 口径、canary 数量、预算参数的变更，必须走变更记录并重跑受影响门槛；
- 不得为了通过而删除 `N/A`、`INCONCLUSIVE`、`survived`、失败证据；
- 不得把 402/small34/quotation 的回归绿写成语义完备；
- 不得用旧结构判据读数替代 G2/G3；
- 任何超出 CPython 3.11.7 / J v1 的结论，另立版本并重跑。
