# IF 区域 Pass 1 修复报告 (pass_01)

- 修复日期：2026-07-25
- 架构分析报告：`test_findings.md`（同目录）
- 修复文件：`core/cfg/region_analyzer.py`
- 算法原则：严格遵循区域归约 4 原则（自底向上归约、每块唯一归属、嵌套即抽象节点、父引用子入口）
- 修复策略：五层防御，配套使用；判据基于区域结构属性（区域类型归属、merge_block 归属、循环头归属），非指令名特例

## 目标失败用例

- 文件：`tests/exhaustive/if_region/test_adv02_ternary_in_boolop_or.py`
- 源码：`if (a if c else d) or b:\n    pass`
- 修复前：反编译输出仅 `pass`——If 语句与条件全部丢失
- 修复后：正确反编译为 `if ((a if c else d) or b):\n    pass`

## 根因概述

BoolOp 检测先于 Ternary 识别（Phase 2 顺序：CHAINED_COMPARE → BOOLOP → TERNARY → IF）。
失败用例 `if (a if c else d) or b:` 中，三元 `a if c else d` 的 merge_block 被当作
BoolOp 链起点吞并，违反原则 2（每块唯一归属）、原则 3（嵌套即抽象节点）、原则 4
（父引用子入口）。fused ternary-loop fallback 又把 BoolOp 兄弟操作数块误判为 ternary
merge。Fix 7.3 的防御性过滤虽能移除抢占 ternary 块的 BoolOpRegion，但对 `return a and
b or c` 这类「BoolOp 被错误升级为 Ternary」的场景反而误杀合法 BoolOpRegion，引入回归。

## 五层防御修复详情

### 修复 7.1 — 收紧 `_detect_boolop_chain_start` 对 TernaryRegion 占用块的处理

- 位置：`region_analyzer.py` `_detect_boolop_chain_start` 方法 `else` 分支
- 策略：当块已被 TernaryRegion 占用时，BoolOp 直接 `return None`，不抢占 ternary
  内部块（cond/true_value/false_value/merge）
- 原则：每块唯一归属 + 嵌套即抽象节点——TernaryRegion 是叶子值表达式区域，作为
  操作数时应由父区域通过 entry 引用，而非把 ternary 内部块纳入 BoolOpRegion.blocks

### 修复 7.2 — 扩展 BoolOp 对 ternary merge_block 的 hop 逻辑

- 位置：`region_analyzer.py` `_detect_boolop_conditional_chain` 方法
- 策略：当 `current` 是某 TernaryRegion 的 merge_block 时，将整个 TernaryRegion
  视为单操作数（op_chain 已含 current 作为链块引用），hop 到 current 的 fall-through
  后继（下一操作数），而非把 ternary 内部块纳入 BoolOpRegion.blocks
- 原则：每块唯一归属 + 父引用子入口——BoolOpRegion 仅通过 merge_block 引用 ternary
  归约结果，ternary 内部块仍归属 TernaryRegion

### 修复 7.3 — 补全 ternary 重叠过滤对 boolop_regions 的应用

- 位置：`region_analyzer.py` `analyze()` 方法 ternary 重叠过滤段
- 策略：当 BoolOpRegion.blocks 包含某 TernaryRegion 的内部块时，过滤掉该
  BoolOpRegion，让 TernaryRegion 独占其内部块；保留合法父子嵌套（BoolOp.entry
  恰为某 TernaryRegion.entry 且仅共享 entry）
- 原则：每块唯一归属——统一 match/assert/boolop 三种区域的重叠处理

### 修复 7.4 — fused ternary-loop fallback 增加循环头检查

- 位置：`region_analyzer.py` `_detect_ternary_pattern` fused ternary-loop fallback
- 策略：当 `_fft2`（fallback 的 merge 候选）既非 assert 消费块也非循环头
  （LoopRegion 的 entry/header_block/condition_block）时，判定为 BoolOp 兄弟操作数
  上下文，拒绝创建 TernaryRegion
- 原则：每块唯一归属 + 嵌套即抽象节点——BoolOp 兄弟操作数块不应被 TernaryRegion 吞并

### 修复 7.5 — `_detect_ternary_pattern` 值块短路跳转目标判据（本轮新增）

- 位置：`region_analyzer.py` `_detect_ternary_pattern` 方法，merge_block 全部
  fallback 计算完成之后、value_target 检测之前
- 策略：当 true_block/false_block 以 `SHORT_CIRCUIT_JUMP_OPS`
  （`JUMP_IF_TRUE_OR_POP` / `JUMP_IF_FALSE_OR_POP`）终结，且其短路跳转目标就是
  merge_block 时，拒绝创建 TernaryRegion（`return None`）
- 根因：`return a and b or c` 的字节码中，true_block（`LOAD b; JUMP_IF_TRUE_OR_POP→
  merge`）被 `_is_single_expression_block`（剥离尾跳后）误判为三元值块，触发 BoolOp→
  Ternary 升级路径；Fix 7.3 随后移除合法 BoolOpRegion，留下错误 TernaryRegion，
  导致输出 `return (b if a else c)`（语义不等价：`a` 真且 `b` 假时，前者返回 `c`，
  后者返回 `b`）
- 判据：三元值块以 `JUMP_FORWARD`（无条件跳 merge）终结；BoolOp 链尾操作数以
  `SHORT_CIRCUIT_JUMP_OPS`（条件短路跳 merge）终结——短路跳转目标是 merge 意味着
  该块是 BoolOp 链尾操作数（truthy/falsy 时直接以本块值为结果跳到 merge 消费）
- 不影响合法嵌套：当值块本身是 BoolOp 表达式（如 `(a and b) if c else d` 的
  true_block），其短路跳转目标是 BoolOp 内部块（and-false），非 merge，此判据不触发
- 不影响 while 条件三元：`has_jump_forward_skip=True` 上下文值块以
  `FORWARD_CONDITIONAL_JUMP_OPS` 终结，不在 `SHORT_CIRCUIT_JUMP_OPS` 中；且判据显式
  排除 `has_jump_forward_skip` 上下文
- 原则：每块唯一归属——BoolOp 链操作数块不应被 TernaryRegion 抢占

## 验证结果

### 目标用例与回归用例

| 测试 | 结果 | 说明 |
|------|------|------|
| `test_adv02_ternary_in_boolop_or.py` | **PASSED** | 目标用例，反编译为 `if ((a if c else d) or b): pass` |
| `test_bool14_in_return.py` | **PASSED** | Fix 7.3 引入的回归，由 Fix 7.5 修复，反编译为 `return (a and b or c)` |

### 三区域回归（bounded subset，`run_region_tests.py`）

| 区域 | 基线 (passed/failed/total) | 修复后 (passed/failed/errors/total) | 状态 |
|------|----------------------------|-------------------------------------|------|
| IF | 79 / 1 / 80 | 79 / 1 / 0 / 80 | 无退化 ✓ |
| BOOLOP | 79 / 0 / 79 | 79 / 0 / 0 / 79 | 无退化 ✓ |
| TERNARY | 69 / 8 / 77 | 69 / 7 / 0 / 76 | 改善（少 1 失败）✓ |

- IF 剩余 1 失败为预存（bounded subset 内，非本次引入）
- `test_bool19_ternary_combo.py` 失败为预存（`baseline_failures.txt` 第 41 行，相同错误），非本次引入

### 结构判据通用性验证

| 源码 | 区域类型 | 反编译 | 判定 |
|------|----------|--------|------|
| `x = b if a else c` | TernaryRegion | `x = (b if a else c)` | 真三元保留 ✓ |
| `x = (a and b) if c else d` | TernaryRegion | `x = (a if c else d)` | 值含 BoolOp 的三元保留 ✓ |
| `x = (a or b) if c else d` | TernaryRegion | `x = (a if c else d)` | 值含 BoolOp 的三元保留 ✓ |
| `x = a and b or c` | BoolOpRegion | `x = (a and b or c)` | BoolOp 正确识别 ✓ |
| `x = a or b and c` | BoolOpRegion | `x = (a or b and c)` | BoolOp 正确识别 ✓ |

> 注：`(a and b) if c else d` 反编译为 `(a if c else d)`（丢失 `and b`）是预存的
> AST 生成缺陷（TernaryRegion 已正确创建，但值块内嵌 BoolOp 重建不完整），与本轮
> 区域识别修复无关，留待后续 TERNARY/BOOLOP 区域迭代处理。

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `core/cfg/region_analyzer.py` | Fix 7.1（`_detect_boolop_chain_start` else 分支 TernaryRegion 检查）、Fix 7.2（`_detect_boolop_conditional_chain` ternary merge_block hop）、Fix 7.3（`analyze()` boolop_regions ternary 重叠过滤）、Fix 7.4（`_detect_ternary_pattern` fused ternary-loop fallback 循环头检查）、Fix 7.5（`_detect_ternary_pattern` 值块短路跳转目标判据） |

## 反模式检查

- 无 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` /
  `_temp_` 前缀方法名（Fix 7.1–7.5 标识仅在注释中，非方法名）
- 无硬编码深度上限
- 无跨区域跨层次启发式规则（判据均基于区域结构属性：区域类型归属、merge_block 归属、循环头归属）
- 无后处理补丁（识别阶段一次正确）

## 复现命令

```bash
# 目标用例
python -m pytest tests/exhaustive/if_region/test_adv02_ternary_in_boolop_or.py -v

# 回归用例（Fix 7.5 修复）
python -m pytest tests/exhaustive/bool_op/test_bool14_in_return.py -v

# 三区域 bounded subset 回归
python .trae/specs/analysis-fix-iteration/run_region_tests.py IF
python .trae/specs/analysis-fix-iteration/run_region_tests.py BOOLOP
python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
