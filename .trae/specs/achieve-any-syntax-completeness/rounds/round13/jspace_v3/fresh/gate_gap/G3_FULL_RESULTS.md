# G3 全量变异测试结果（1086 个带 calls 的 J 条目）
## 一、case 层面
| 项 | 数 |
|---|---:|
| 生成 case 总数 | 1086 |
| 可评估（baseline EQUAL） | **912** |
| 基线不可评估（`ABORTED_BASELINE`） | **174** |
| 无变异（`NO_MUTANTS`） | 0 |
| 崩溃（无结果） | 0 |

基线不可评估原因分布（原文）：

- `基线 DIFFERENT（产品经 ast.unparse 往返后已不等价）` × 138
- `load/execute 失败：original artifact did not load/execute` × 36

## 二、mutant 层面（原始判定 → 按裁决离线重分类）

| 状态 | 原始 | 重分类后 |
|---|---:|---:|
| KILLED | 17185 | **17284** |
| MISSED | 0 | **0** |
| EQUIVALENT | 0 | 0 |
| FALSE_KILL | 0 | 0 |
| INCONCLUSIVE | 81 | — |
| ERROR | 18 | — |
| generator_fixes（不入分母） | — | 0 |
| unjudgeable | — | 0 |

重分类明细：崩溃→KILLED **18**、超时→KILLED **81**、生成器失败 0、其它 0

**mutation score（KILLED / (KILLED+MISSED)）= 1.0000**

## 三、结论
- 可评估 case 的 **missed = 0**；分母 = KILLED+MISSED = 17284。
- 基线不可评估的 174 个 case 分两类：**load/execute 失败 36**（原件 pyc 加载失败，与 G1 的 376 条、G2b 的 342 条 ERROR 同源）与 **基线 DIFFERENT 138**（产品经 `ast.unparse` 往返后与原件已不等价——其中含 R7 常量顺序/死常量与可能的往返格式效应，**未逐条定性，不当作产品缺陷计数**）。两类均记 case-level `unjudgeable`，**不计入分子也不伪造成 KILLED**。
- 按 `spec.md` G3 阈值 `missed = 0`：**在可评估范围内达成**；但 G3 整体仍需全量 case 可评估，故**不宣称 G3 PASS**。
