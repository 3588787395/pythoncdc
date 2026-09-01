# 区域反编译 100% 字节码一致性迭代 Spec

## Why

前置 spec `region-decompile-perfection` 与 `refine-region-algorithm` 已完成，达到：
- 测试矩阵 99.95%（2067/2068，**te046 暂缓**为「CPython 3.11+ multi-context with 字节码不可区分」已知限制）
- match_region 独立测试 100%（198/198，2 skipped 为 m085 已知限制）
- 算法符合度 FULLY COMPLIANT（无 WARN、无硬编码深度上限）
- 19 个识别/生成方法 docstring 符合统一模板
- `isinstance.*Region` 计数 116（原目标 < 20 未达成；Priority 3 批量替换导致 267 回归已回滚）

**新发现**：对 te046 的根因复检表明，前置 spec 的「CPython 不可区分」结论**不成立**——
`with open('a') as fa: with open('b') as fb: ...`（嵌套）与
`with open('a') as fa, open('b') as fb: ...`（多上下文）的**指令流完全相同**（均为 75 条），
仅异常表二进制布局不同。但反编译器当前产出的输出含**多余 `if True: pass` 语句**：

```python
try:
    with open('a') as fa, open('b') as fb: x = (fa.read() + fb.read())
except: x = ''
if True:        # ← 多余，源自对隐式 module-level return None 块的误识别
    pass
```

去除 `if True: pass` 后重编译的指令数为 71（与原始匹配），当前反编译输出重编译为 67（少 4 条
`LOAD_CONST None + RETURN_VALUE + COPY + POP_EXCEPT + RERAISE`，因 `if True: pass` 错误吞并了
隐式返回块的字节码）。**te046 是真实可修复缺陷**，应纳入本 spec 处理。

同时，116 处 `isinstance.*Region` 仍超出原目标 < 20，且 `region_analyzer.py`（~13000 行）
存在可继续精简的分支与代码复杂度。本 spec 在保持现有 99.95% 基线的前提下，**驱动迭代循环**
使反编译器达到 100% 成功率与字节码完全匹配，并进一步降低复杂度，使所有识别/生成方法完全
符合区域归约算法 4 条核心原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口）。

## What Changes

- **修复 te046**：定位 spurious `if True: pass` 的根因（隐式 module-level return None 块被
  IfRegion 误识别），在识别阶段正确处理该块（归属父级 SequenceRegion 或 WithRegion 的隐式
  return，而非独立 IfRegion），重写相关 docstring
- **重新校核各区域 docstring**：以 100% + 字节码完全匹配为目标，对 10 个 `_identify_*_regions`
  与 9 个 `_generate_*` 方法的 docstring 逐个回归，更新「6. 已知失败模式」与「字节码一致性约束」
  小节，确保注释与代码一致
- **降低 isinstance 分支**：在 Priority 1+2 基础上，采用新策略（visitor 模式 / 分派表 / 多态方法
  扩展）将 `isinstance.*Region` 从 116 降至 < 20，每步小步快跑 + 全量回归
- **降低代码复杂度与分支**：审计 `region_analyzer.py` 与 `region_ast_generator.py`，合并重复
  分派逻辑、消除冗余分支、移除已废弃的旧路径，**不**新增对外 API
- **迭代循环**：对每一区域类型执行「测试 → 字节码 diff → 修正识别逻辑 → 重写注释 → 回归测试」
  循环，直至 100% 通过率且所有失败用例 `_compare_code_objects()` 返回 `None`
- **保持基线不退化**：任何修改后 `run_test_matrix.py` 全量通过率 **MUST NOT** 低于 99.95%
  （即 2067/2068，te046 修复后达到 2068/2068 = 100%），match_region 保持 198/198

## Impact

- **Affected specs**:
  - `region-decompile-perfection`（已完成，作为基线参考）
  - `refine-region-algorithm`（已完成，作为基线参考）
- **Affected code**:
  - `core/cfg/region_analyzer.py`（~13000 行）— te046 修复 + isinstance 降低 + 复杂度精简
  - `core/cfg/region_ast_generator.py`（~15500 行）— 配合识别阶段调整，docstring 校核
  - `tests/exhaustive/run_test_matrix.py`（仅验证用，不修改）
  - `tests/exhaustive/match_region/`（仅验证用，不修改）
  - `tests/exhaustive/try_except/test_te046.py`（仅验证用，不修改）
- **Algorithm compliance**：保持 FULLY COMPLIANT（4 条核心原则 + 无 WARN + 无硬编码深度上限）
- **Risk**：te046 修复触及 try/with 复合嵌套的识别；isinstance 替换历史上曾导致 267 回归，
  需小步快跑 + 每步回归

## ADDED Requirements

### Requirement: te046 修复（spurious if True: pass）

系统 **SHALL** 正确处理隐式 module-level `return None` 块（位于 `with` 清理块与外层异常处理
入口之间），不将其误识别为 IfRegion，不生成 spurious `if True: pass` 语句。

#### Scenario: te046 反编译输出无 spurious if True: pass
- **WHEN** 反编译 te046 源码（`try: with open('a') as fa: with open('b') as fb: x = ...; except: x = ''`）
- **THEN** 反编译结果**MUST NOT**包含 `if True:` 语句
- **AND** 反编译结果重编译后，`_compare_code_objects(original, recompiled)` 返回 `None`
- **AND** 过滤后指令数 = 71（与原始一致）

#### Scenario: 隐式 module-level return 块的归属
- **WHEN** 识别阶段遇到位于 `with` 清理块末尾、后继为异常处理入口的 `LOAD_CONST None + RETURN_VALUE`
  块
- **THEN** 该块**SHALL**归属于最近的 SequenceRegion 或 WithRegion 的隐式 return 语义
- **AND** **MUST NOT**作为独立 IfRegion 创建

### Requirement: isinstance.*Region < 20

`region_analyzer.py` 中的 `isinstance.*Region` 出现次数 **SHALL** < 20。

#### Scenario: isinstance 数量达标
- **WHEN** 执行 `grep -c "isinstance.*Region" core/cfg/region_analyzer.py`
- **THEN** 输出**MUST** < 20

#### Scenario: 多态分派优先
- **WHEN** 方法需要按区域类型执行不同逻辑
- **THEN** **SHALL**优先调用 Region 子类的多态方法或分派表查找
- **AND** **MUST NOT**使用 `isinstance` 链式 if/elif 分派

### Requirement: 字节码完全一致性验证（每区域）

每一次修改识别/生成逻辑后，**SHALL**对受影响的区域类型执行：
1. 区域级测试集（如 `--category with_region`）通过率 = 100%
2. 失败用例的 `_compare_code_objects()` 返回 `None`
3. 全量 `run_test_matrix.py` 通过率 **MUST NOT** 退化

#### Scenario: 区域级回归
- **WHEN** 修改 `_identify_with_regions` 或 `_generate_with`
- **THEN** `python tests/exhaustive/run_test_matrix.py --category with_region` 通过率 **MUST** = 100%
- **AND** `python tests/exhaustive/run_test_matrix.py --category try_except` 通过率 **MUST** = 100%（te046 修复后）
- **AND** 全量 `run_test_matrix.py` 通过率 **MUST NOT** < 99.95%

### Requirement: 注释迭代校核

每个 `_identify_*_regions` / `_generate_*` 方法的 docstring **SHALL**经过本轮迭代校核，
确保「6. 已知失败模式」小节列出**所有当前测试矩阵中失败的用例**（te046 修复后应为空或仅 m085），
且修复状态与代码实际状态一致。

#### Scenario: 失败模式小节准确
- **WHEN** 检查任意 `_identify_*_regions` 的 docstring「6. 已知失败模式」
- **THEN** 列出的用例**MUST**与实际测试矩阵失败列表一致
- **AND** 每个用例的修复状态（已修复 / 暂缓 / 已知限制）**MUST**与代码状态一致

## MODIFIED Requirements

### Requirement: 区域识别算法

区域识别遵循自底向上归约顺序，每个块在任意层级只属于一个区域，嵌套区域在父区域中作为
单个抽象节点表示，父区域引用子区域入口块。识别阶段一次正确，不依赖后处理修正。所有方法
不包含硬编码深度上限。**新增**：隐式 module-level return 块（`LOAD_CONST None + RETURN_VALUE`
位于结构末尾、后继为异常处理入口）按其语义归属，不作为独立 IfRegion 创建。

### Requirement: 注释模板（6 节识别 / 4 节生成）

10 个 `_identify_*_regions` 方法的 docstring 保持 6 节模板
（【区域类型】/ 1.算法描述 / 2.字节码模式 / 3.边界条件 / 4.归约语义 / 5.AST映射 / 6.已知失败模式），
9 个 `_generate_*` 方法保持 4 节模板
（输入契约 / AST映射规则 /子区域处理 / 字节码一致性约束）。**新增**：本轮迭代后，「6. 已知失败
模式」与「字节码一致性约束」**MUST**反映 100% 通过率与字节码完全匹配状态。

## REMOVED Requirements

### Requirement: te046 暂缓为已知限制

**Reason**: 前置 spec 将 te046 标记为「CPython 3.11+ multi-context with 字节码不可区分」并暂缓，
但根因复检表明此结论不成立——指令流可区分（多上下文 with 与嵌套 with 指令完全一致，仅异常表
布局不同），且当前反编译输出含 spurious `if True: pass`（源自隐式 module-level return 块的误识别），
是真实可修复缺陷。
**Migration**: 在识别阶段正确处理隐式 return 块的归属（不作为 IfRegion 创建），并在 docstring
中更新失败模式记录。
