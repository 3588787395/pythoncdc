# 区域模式反编译逻辑完善规范

## Why
当前反编译器经过21个Phase的系统性优化，整体通过率从67.6%提升至~81-83%。但最新实测发现存在**显著回归**（从~257f增至~340f，整体降至~76.2%），主要原因是BoolOp区域灾难性回退(+41f)、While循环大幅回退(+14f)和Assert区域大幅回退(+11f)。需要先诊断并修复这些回归问题，然后继续深度优化直到100%成功率和字节码完全匹配。

## What Changes
- **Phase 22（回归修复）**: 诊断并修复3个P0级回归区域（BoolOp/While/Assert）和2个P1级回退区域（Try/For）
- **Phase 23（深度优化）**: 在回归修复基础上，针对"差N条指令"模式、UNARY_NOT丢失、Ternary边界、If死代码恢复等进行定向优化
- **Phase 24（架构突破）**: 动态优先级引擎、控制流跟踪、Match独立管道等架构级重构
- 为 `RegionAnalyzer` 和 `RegionASTGenerator` 中持续发现的问题添加修复代码
- 为每个修复添加对应的反编译逻辑注释
- 迭代测试-修正循环，直到所有区域测试100%通过且字节码完全匹配

## Impact
- Affected specs: 所有9种区域类型的识别与生成逻辑
- Affected code:
  - `core/cfg/region_analyzer.py` - BoolOp/While/Assert识别方法 + 辅助方法
  - `core/cfg/region_ast_generator.py` - BoolOp/While/Assert生成方法 + generate()入口
  - 测试文件: `tests/exhaustive/` 下9个区域子目录 + `basic/` (assert测试)

## ADDED Requirements

### Requirement: 回归修复（Phase 22 P0）
系统 SHALL 修复以下区域的测试回归，恢复至Phase 21报告的水平：
- **BoolOp区域**: 从76f修复至≤60f（≥65%通过率），恢复Phase 18b的35f(73.5%)水平
- **While循环**: 从45f修复至≤35f（≥70%通过率），恢复Phase 18b的31f(74.2%)水平
- **Assert区域**: 从16f修复至≤6f（≥75%通过率），恢复Phase 18a的5f(80.8%)水平

#### Scenario: BoolOp回归修复
- **WHEN** 运行BoolOp区域132个测试用例时
- **THEN** 失败数≤60（≥95%的原通过测试恢复）

### Requirement: 回归修复（Phase 22 P1）
系统 SHALL 修复Try-except和For循环的轻微回退：
- **Try-except**: 从44f修复至≤38f（≥83%）
- **For循环**: 从11f修复至≤9f（≥94%）

### Requirement: 深度优化目标（Phase 23）
在回归修复完成后，系统 SHALL 通过以下优化将整体通过率提升至85-88%：
- While"差N条指令"统一修复（预期-15f）
- UNARY_NOT丢失修复（预期-6f）
- Ternary边界精炼（预期-5f）
- If死代码恢复尝试（预期-8f）
- Match is None降级增强（预期-5f）
- For/With/Assert边缘清理（预期-5f）

### Requirement: 架构突破目标（Phase 24）
系统 SHALL 通过架构级重构达到90%+：
- BoolOp动态优先级引擎（预期-25f）
- While控制流统一跟踪（预期-15f）
- Match Pattern独立管道v2（预期-15f）

## MODIFIED Requirements

### Requirement: 区域归约算法一致性（持续有效）
所有新增修复 SHALL 严格遵循区域归约算法：
1. Phase 1（低层）：TRY > LOOP > WITH/MATCH/ASSERT，按优先级识别
2. Phase 2（高层）：CHAIN_CMP > BOOLOP > TERNARY > CONDITIONAL
3. Phase 3（底层）：SEQUENCE覆盖未归约块
4. 区域不重叠原则：每个基本块只属于一个区域
5. 自底向上归约：内层先识别，外层后识别

### Requirement: 反编译逻辑注释规范（持续有效）
每个新增修复的代码 SHALL 包含结构化注释：
1. 根因分析 - 为什么会出现这个bug
2. 字节码模式 - 触发bug的字节码特征
3. 修复策略 - 如何修复及为什么这样修复
4. 归约符合度 - 修复如何符合区域归约理论
5. 影响范围 - 哪些测试受影响

## REMOVED Requirements
（无移除需求）

---

## 当前实测基线（Phase 34 Start, 2026-05-14）

| 区域 | 失败 | 通过 | 总计 | 通过率 | 优先级 |
|------|------|------|------|--------|--------|
| basic | 5 | 117 | 122 | **95.9%** | P3 |
| if_region | 34 | 277 | 311 | **89.1%** | P1 |
| while_loop | 8 | 112 | 120 | **93.3%** | P2 |
| for_loop | 12 | 181 | 193 | **93.8%** | P2 |
| try_except | 23 | 207 | 230 | **90.0%** | P1 |
| with_region | 9 | 182 | 191 | **95.3%** | P3 |
| match_region | 20 | 178 | 198 | **89.9%** | P1 |
| boolop | 9 | 123 | 132 | **93.2%** | P2 |
| ternary | 13 | 103 | 116 | **88.8%** | P1 |
| nested | **107** | 178 | 285 | **62.5%** | **P0** 🔥🔥🔥 |
| **总计** | **240** | **1658** | **1898** | **87.4%** | |

## ADDED Requirements (Phase 34+)

### Requirement: 算法驱动的区域归约（Phase 34 核心原则）
系统 SHALL 基于 "No More Gotos" (Launez et al., 2013) 论文的结构化算法核心思想，结合 Python 字节码特性，实现算法驱动的区域归约：

1. **回边检测**：基于支配树的标准回边检测算法（DominatorAnalyzer），替代启发式回边判断
2. **区域分类**：将CFG节点集合分类为有限种区域类型（Block/If/IfElse/IfElseIf/Switch/While/DoWhile/For/NaturalLoop/TryExcept/With/Match/Sequence）
3. **归约**：将识别出的区域归约为单个节点，迭代直到整个CFG归约为一个节点
4. **AST映射**：每个区域类型对应唯一的AST节点类型，映射关系确定不变

#### Scenario: 回边检测正确性
- **WHEN** DominatorAnalyzer计算支配树后
- **THEN** 所有回边（back edge）通过 "边 N→D 其中 D 支配 N" 的数学性质检测，无需启发式规则

#### Scenario: 区域归约完整性
- **WHEN** 对CFG执行区域归约算法
- **THEN** 迭代归约后整个CFG归约为单个节点，无遗漏块

### Requirement: 单向数据流与一次正确（Phase 34 设计约束）
系统 SHALL 遵循以下设计约束：

1. **单向数据流**：分析结果从底层向上层传递，不回溯修正。一旦区域被识别和归约，其分类不再改变
2. **一次正确**：每个结构在识别阶段就正确分类，不需要后处理修正。消除所有 `_fix_*`、`_patch_*`、`_adjust_*` 类方法
3. **算法驱动**：用算法替代模式匹配，用数学性质替代启发式规则。每个识别决策都有明确的算法依据

#### Scenario: 无回溯修正
- **WHEN** 区域识别阶段完成
- **THEN** 不存在任何后处理修正步骤改变已识别区域的类型或边界

### Requirement: Nested区域突破（Phase 34 P0）
系统 SHALL 将nested区域通过率从62.5%提升至≥80%：
- 根因：嵌套区域间的层次关系识别不正确，导致内层区域被外层错误吞噬
- 方案：基于支配树的区域层次化归约，确保内层区域先识别、先归约

#### Scenario: Nested区域改善
- **WHEN** 运行nested区域285个测试用例时
- **THEN** 失败数≤57（≥80%通过率）

### Requirement: If/Try/Ternary/Match区域攻坚（Phase 34 P1）
系统 SHALL 将以下区域通过率提升至≥95%：
- **If条件**：从89.1%提升至≥95%（34f→≤16f）
- **Try-except**：从90.0%提升至≥95%（23f→≤12f）
- **Ternary**：从88.8%提升至≥95%（13f→≤6f）
- **Match区域**：从89.9%提升至≥95%（20f→≤10f）

### Requirement: 反编译逻辑注释完善（Phase 34 持续）
每个区域识别和生成方法 SHALL 包含完整的反编译逻辑注释：
1. **算法描述** - 该方法使用的区域归约算法步骤
2. **字节码模式** - 触发该区域类型的字节码特征（基于CPython编译器行为）
3. **边界条件** - 区域边界的确定规则（基于支配树/回边等数学性质）
4. **归约符合度** - 该方法如何符合 "No More Gotos" 论文的区域归约理论
5. **AST映射规则** - 该区域类型到AST节点类型的确定映射关系

### Requirement: 100%成功率和字节码完全匹配（最终目标）
系统 SHALL 通过迭代测试-修正循环，最终达到：
- 所有区域测试100%通过
- 反编译后重新编译的字节码与原始字节码完全匹配

## 完整演进表

| 区域 | Phase0 | Phase17 | Phase25 | Phase30 | Phase32 | Phase33 | **Phase34基线** | 目标 |
|------|--------|---------|---------|---------|---------|---------|-----------------|------|
| Basic | - | - | - | - | - | - | **5f (95.9%)** | 0f |
| For | 62f | 19f | 14f | 14f | 14f | 12f | **12f (93.8%)** | 0f |
| While | 66f | 50f | 34f | 23f | 19f | 8f | **8f (93.3%)** | 0f |
| Try | 54f | 35f | 35f | 28f | 28f | 23f | **23f (90.0%)** | 0f |
| With | 37f | 9f | 9f | 9f | 9f | 9f | **9f (95.3%)** | 0f |
| Match | 74f | 51f | 47f | 39f | 29f | 20f | **20f (89.9%)** | 0f |
| If | 90f | 48f | 51f | 48f | 38f | 34f | **34f (89.1%)** | 0f |
| BoolOp | 12f | 64f | 6f | 8f | 8f | 9f | **9f (93.2%)** | 0f |
| Ternary | 32f | 19f | 13f | 13f | 13f | 13f | **13f (88.8%)** | 0f |
| Nested | - | - | - | - | - | - | **107f (62.5%)** | 0f |
| **总计** | **~427f** | **306f** | **~225f** | **~182f** | **~153f** | **~129f** | **240f (87.4%)** | **0f** |

### 历史里程碑

```
Phase 0:    ~427f (~67.6%)   ← 原始基线
Phase 17:   306f (78.9%)     ← 架构重构与收敛
Phase 25:   ~225f (86.8%)    ← BoolOp突破95.5%
Phase 30:   ~182f (89.1%)    ← While突破80.8%
Phase 32:   ~153f (91.7%)    ← If突破87.5%! 净-28f!
Phase 33:   ~129f (~90.3%)   ← While突破92.7%! 净-24f!
Phase 34:   240f (87.4%)     ← 新基线(含nested区域), 算法驱动归约
                         目标: 0f (100%)
```
