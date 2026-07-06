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

## 当前实测基线（Phase 35 Start, 2026-05-16）

| 区域 | 失败 | 通过 | 总计 | 通过率 | 优先级 |
|------|------|------|------|--------|--------|
| basic | 20 | 73 | 96 | **76.0%** | P2 |
| if_region | 15 | 290 | 311 | **95.2%** | P2 ✅ |
| while_loop | 6 | 103 | 120 | **85.8%** | P2 ✅ |
| for_loop | 12 | 180 | 193 | **93.8%** | P2 |
| try_except | 21 | 202 | 230 | **90.6%** | P1 |
| with_region | 9 | 182 | 191 | **95.3%** | P3 ✅ |
| match_region | 3 | 176 | 198 | **98.3%** | P3 ✅ 🎉 |
| boolop | 9 | 123 | 132 | **93.2%** | P2 |
| ternary | 8 | 81 | 116 | **69.8%** | P1 |
| nested | **89** | 176 | 285 | **62.5%** | **P0** 🔥🔥🔥 |
| **总计** | **192** | **1536** | **1832** | **88.9%** | |

### Phase 34→35 关键改善
- match_region: 19f→3f (-16f!) 🏆🏆🏆 (pattern_parser改进+REGION_TYPE_ALTERNATIVES)
- if_region: 27f→15f (-12f!) 🏆🏆 (IF_ELIF_CHAIN修复+common_blocks+elif链检测)
- while_loop: 10f→6f (-4f) 🏆 (BoolOp循环体后处理+条件链防护)
- nested: 93f→89f (-4f) (else块过滤+层次修复)
- for_loop: 12f恢复 (LOOP_BACK_EDGE→Continue误生成已修复)

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

### Requirement: Phase 45 区域归约算法驱动完善
系统 SHALL 基于 "No More Gotos" 论文的区域归约算法，对每一区域执行以下步骤：
1. **分析区域失败模式** — 将每个区域的失败测试按错误类型分类
2. **规划反编译逻辑** — 基于区域归约理论，为每种失败模式设计修复方案
3. **写入识别方法注释** — 将反编译逻辑以结构化注释写入对应的识别方法
4. **执行测试验证** — 运行区域测试，验证成功率和字节码一致性
5. **修正反编译逻辑** — 根据错误修正反编译逻辑，重新写入注释
6. **完善代码** — 完成相应代码修改
7. **持续迭代** — 直到100%成功率和字节码完全匹配

#### Scenario: if60ifelsebreak回归修复
- **WHEN** 循环内if-else含break时
- **THEN** 反编译生成的指令数与原始字节码匹配（18→15修复为15）

#### Scenario: if61ifelsecontinue COMPARE_OP正确
- **WHEN** 循环内if-else含continue时
- **THEN** COMPARE_OP操作符与原始字节码一致（`>`不被错误取反为`<=`）

#### Scenario: BoolOp-If冲突消解
- **WHEN** `if a and b:` 模式的字节码与 `return a and b` 几乎相同时
- **THEN** 基于上下文正确识别为IfRegion而非BoolOpRegion

### Requirement: Phase 48 区域归约算法全区域完善
系统 SHALL 基于 "No More Gotos" 论文的区域归约算法，对每一区域执行以下完整循环：
1. **分析区域模式** — 将每个区域的失败测试按字节码模式分类，识别根因
2. **规划反编译逻辑** — 基于区域归约理论，为每种失败模式设计修复方案
3. **写入识别方法注释** — 将反编译逻辑以结构化注释写入对应的识别方法和生成方法
4. **执行测试验证** — 运行区域测试，验证成功率和字节码一致性
5. **修正反编译逻辑** — 根据错误修正反编译逻辑，重新写入注释
6. **完善代码** — 完成相应代码修改
7. **持续迭代** — 直到100%成功率和字节码完全匹配

核心设计原则：
- **区域化分析**：基于编译器理论中的区域分析算法，将CFG分解为层次化的区域
- **单向数据流**：分析结果从底层向上层传递，不回溯修正
- **一次正确**：每个结构在识别阶段就正确分类，不需要后处理修正
- **算法驱动**：用算法替代模式匹配，用数学性质替代启发式规则

#### Scenario: BoolOp短路路径重复生成修复
- **WHEN** BoolOpRegion嵌套在WithRegion/TryExceptRegion中时
- **THEN** BoolOpRegion的blocks不被父区域重复生成（P0修复：_generate_boolop标记generated_blocks + _generate_with识别BoolOpRegion子区域）

#### Scenario: With区域BoolOp/Ternary子区域处理
- **WHEN** WithRegion包含BoolOpRegion或TernaryRegion子区域时
- **THEN** _generate_with正确识别并委托生成，不将子区域blocks作为简单语句重复生成

#### Scenario: 嵌套While-While-Break正确归约
- **WHEN** 内层while break的跳转目标与外层while条件重合时
- **THEN** break正确归约到内层循环，不与外层循环条件混淆

#### Scenario: Try-Except中continue/break正确分类
- **WHEN** try-except块位于循环内部且包含continue/break时
- **THEN** continue/break的角色基于跳转目标正确分类，不因异常处理边界而误判

#### Scenario: 所有区域100%成功率
- **WHEN** 运行全部10个区域的测试套件时
- **THEN** 所有测试通过，反编译后重新编译的字节码与原始字节码完全匹配

## 完整演进表

| 区域 | Phase0 | Phase17 | Phase25 | Phase33 | Phase41 | Phase44 | Phase45 | **Phase48基线** | 目标 |
|------|--------|---------|---------|---------|---------|---------|---------|-----------------|------|
| Basic | - | - | - | - | 7f | 7f | 7f | **0f (100%)** | 0f ✅ |
| If | 90f | 48f | 51f | 34f | 50f | 44f | 9f | **6f (98.0%)** | 0f |
| For | 62f | 19f | 14f | 12f | 7f | 6f | 7f | **3f (98.4%)** | 0f |
| While | 66f | 50f | 34f | 8f | 10f | 10f | 12f | **5f (95.3%)** | 0f |
| Try | 54f | 35f | 35f | 23f | 21f | 21f | 21f | **11f (95.0%)** | 0f |
| With | 37f | 9f | 9f | 9f | 9f | 9f | 9f | **9f (95.3%)** | 0f |
| Match | 74f | 51f | 47f | 20f | 4f | 4f | 4f | **4f (97.8%)** | 0f |
| BoolOp | 12f | 64f | 6f | 9f | 9f | 9f | 9f | **8f (93.9%)** | 0f |
| Ternary | 32f | 19f | 13f | 13f | 8f | 8f | 8f | **8f (91.0%)** | 0f |
| Nested | - | - | - | - | 87f | 81f | 81f | **73f (73.1%)** | 0f |
| **总计** | **~427f** | **306f** | **~225f** | **~129f** | **212f** | **199f** | **167f** | **127f (93.0%)** | **0f** |

### 历史里程碑

```
Phase 0:    ~427f (~67.6%)   ← 原始基线
Phase 17:   306f (78.9%)     ← 架构重构与收敛
Phase 25:   ~225f (86.8%)    ← BoolOp突破95.5%
Phase 30:   ~182f (89.1%)    ← While突破80.8%
Phase 32:   ~153f (91.7%)    ← If突破87.5%! 净-28f!
Phase 33:   ~129f (~90.3%)   ← While突破92.7%! 净-24f!
Phase 34:   240f (87.4%)     ← 新基线(含nested区域), 算法驱动归约
Phase 41:   212f (88.2%)     ← Return→Break值保持修复, for_loop 96.3%
Phase 44:   199f (88.9%)     ← 循环条件分支修复, for_loop 96.9%
Phase 45:   167f (90.8%)     ← BoolOp-If冲突消解! if_region 97.1%! 净-33f!
Phase 47:   127f (93.0%)     ← while_loop修复+BoolOp-If消解, basic 100%!
Phase 49:   39f (97.9%)      ← match+try修复前基线
Phase 50:   36f (98.1%)      ← match+try嵌套修复(m054/m061/m069), match 7f→4f
                         目标: 0f (100%)
```

### Phase 50 当前基线（2026-06-04 实测）

| 区域 | 失败 | 通过 | 总计 | 通过率 | 优先级 |
|------|------|------|------|--------|--------|
| basic | 0 | 122 | 122 | **100%** | ✅ |
| if_region | 0 | 311 | 311 | **100%** | ✅ |
| while_loop | 3 | 117 | 120 | 97.5% | P1 |
| for_loop | 4 | 189 | 193 | 97.9% | P1 |
| try_except | 6 | 224 | 230 | 97.4% | P1 |
| with_region | 2 | 189 | 191 | 99.0% | P2 |
| match_region | 4 | 194 | 198 | 98.0% | P2 |
| boolop | 2 | 130 | 132 | 98.5% | P2 |
| ternary | 7 | 109 | 116 | 94.0% | P1 |
| nested | 8 | 277 | 285 | 97.2% | P2 |
| **总计** | **36** | **1862** | **1898** | **98.1%** | |

### Phase 50 剩余36个失败测试详细列表

#### while_loop (3f)
- while06_false — `while False: x=1` CPython优化为NOP，需合成While节点
- while13_while_return — while else中return None被has_trailing_return_none过滤
- wl05whiletrue — `while True: break` CPython优化为NOP，需合成While节点

#### for_loop (4f)
- fl46forreturn_n — SWAP+POP_TOP+RETURN_VALUE处理错误
- fl51forbreaknestedif_n/x — for+break+嵌套if
- for16_for_if — ternary vs if-else选择错误

#### try_except (6f)
- te080, te081, te100 — try-finally finally块重复/丢失
- te104 — 嵌套try-except handler排序
- try16_multi_nested — 复杂try嵌套
- try20_complex_pattern — 复杂try模式

#### with_region (2f)
- w058 — async with
- w30withcustomctx — 自定义上下文管理器

#### match_region (4f)
- m075, m083 — 指令数不匹配
- m106 — guard boolop
- m107 — match in func return

#### boolop (2f)
- bo42 — BoolOp in listcomp
- bo43 — complex not-and-or

#### ternary (7f)
- te04_a/n — ternary func param
- ternary11_in_if, ternary12_in_while, ternary13_in_for_iter — ternary在控制结构中
- ternary17_in_lambda — ternary在lambda中
- ternary20_complex_practical — 复杂实用模式

#### nested (8f)
- n09 — while+try+except
- n10_a/b — for+if+for+break
- n11_a/b — while+if+while+break
- n13_a/n — try+for+if+break
- n15 — while+if+try+except
```

### Phase 48 失败模式分类（127f详细分析）

#### P0: Nested区域 (73f, 57.5%的失败)
- **BoolOp/Ternary重复生成** (~12f): with_boolop(3), try_boolop(3), try_ternary(3), with_ternary(3) — P0修复目标
- **循环嵌套break/continue误分类** (~15f): n11, n13, n18, n23, while_boolop, while_if, while_match, while_ternary
- **Match嵌套body丢失** (~15f): match_if(3), match_match(3), match_boolop(3), match_ternary(3), match_while(3)
- **if-elif-in-while结构错误** (~6f): n29(3), n17(2), n01(3=if43)
- **深层嵌套归约不完整** (~9f): n35(3), n14(2), n15(2), n09(1), n07(1), n10(2)

#### P1: Try区域 (11f)
- **for-try-continue中continue→break误判** (~3f): te047, te083, te050
- **嵌套try-except handler排序** (~3f): te104, try15, try20
- **try-finally finally块重复/丢失** (~3f): te080, te081, te100
- **复杂try模式** (~2f): try11(32vs42), try16(语法错误)

#### P1: With区域 (9f)
- **with+boolop/ternary重复生成** (~3f): w035, w043, w30 — P0修复目标
- **with+try嵌套** (~3f): w058, w079, w080
- **with+循环嵌套** (~3f): w099, w100, w102

#### P2: BoolOp区域 (8f)
- **混合and/or链segment构建** (~3f): bo24 or-and-or (16vs14)
- **BoolOp-If冲突(反向)** (~3f): bo31 and-in-if (未找到BOOL_OP)
- **ListComp中BoolOp** (~1f): bo42
- **复杂not-and-or** (~1f): bo43 (19vs11)

#### P2: Ternary区域 (8f)
- **ternary在if/while/for/try/lambda中** (~5f): ternary11-13, ternary15, ternary17
- **嵌套code object参数不匹配** (~2f): te04×2
- **复杂实用模式** (~1f): ternary20

#### P2: While区域 (5f)
- **while False/while True识别** (~2f): while06, wl05
- **while-return/raise** (~2f): while13, while14
- **复杂状态机** (~1f): while20

#### P2: If区域 (6f)
- **if-in-while指令数不匹配** (~3f): if43 (22vs24)
- **ternary-in-if赋值丢失** (~3f): if72 (14vs9)

#### P3: For区域 (3f)
- **for-return直接** (~1f): fl46forreturn_n
- **for-if嵌套** (~1f): for16
- **复杂body** (~1f): for20

#### P3: Match区域 (4f)
- **guard boolop** (~1f): m106
- **match-in-func-return** (~1f): m107
- **复杂pattern** (~2f): m075, m083
