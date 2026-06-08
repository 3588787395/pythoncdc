# 修复7个嵌套区域测试失败 Spec

## Why
当前 nested 测试 7f/285p (97.5%)，7个失败测试均涉及 try/while/for + if + break 的复杂嵌套模式，反编译输出存在结构错误（条件反转、语句错位、多余语句等），需要修复区域识别和AST生成逻辑。

## What Changes
- 修复 `_if_generate_then_branch` 中嵌套区域（LoopRegion/TryExceptRegion/WithRegion）的生成逻辑
- 修复 `_generate_loop` 中 for-else 与循环后语句的区分
- 修复 `_process_if_blocks` 中条件 break 的 BoolOp 条件拆分问题
- 修复 `_generate_try` 中 try-except 后多余语句生成
- 修复 `_loop_generate_body` 中循环后语句与 for-else 的混淆
- 修复 while 条件中 BoolOp 链的完整性

## Impact
- Affected specs: nested 区域测试
- Affected code:
  - `core/cfg/region_ast_generator.py` — 主要修改文件
  - `core/cfg/region_analyzer.py` — 仅在必要时修改

## ADDED Requirements

### Requirement: try-for-break 模式正确反编译
系统 SHALL 正确反编译 `try: for v in values: if v is None: break; n = v; except StopIteration: values = []` 模式：
- `if v is None: break` 条件不被反转
- `n = v` 作为循环体语句正确生成（不在 for-else 中）
- 不生成多余的 `else: return None`

#### Scenario: n07 try_for_break_n_stopiteration
- **WHEN** 反编译 `try: for v in values: if v is None: break; n = v; except StopIteration: values = []`
- **THEN** 字节码指令数匹配（26 vs 26，非 26 vs 25）

### Requirement: while-try-except-break 模式正确反编译
系统 SHALL 正确反编译 `while cond: try: stmt; except: stmt; break` 模式：
- try-except 块后不生成多余语句
- break 正确位于 except 子句中

#### Scenario: n09 while_try_except_a_indexerror
- **WHEN** 反编译 `while len(data) > 0: try: a = data.pop(); except IndexError: a = None; break`
- **THEN** 字节码指令数匹配（35 vs 35，非 35 vs 40），无多余 `len(data)` 语句

### Requirement: for-if-for-break 模式正确反编译
系统 SHALL 正确反编译 `for row in matrix: if len(row) > 0: for val in row: if val == target: break; a = row` 模式：
- 内层 for 循环在 if 条件内部
- `a = row` 作为内层 for 循环后的语句（非 for-else）
- 不生成多余的 `if len(row) > 0: pass` 和 `else: return None`

#### Scenario: n10a for_if_for_break_a_b
- **WHEN** 反编译 `for row in matrix: if len(row) > 0: for val in row: if val == target: break; a = row`
- **THEN** 字节码操作码匹配（LOAD_GLOBAL vs LOAD_FAST 不再出现），结构正确

#### Scenario: n10n for_if_for_break_n_m
- **WHEN** 反编译 `for line in data: if line is not None: for elem in line: if elem == search: break; n = line`
- **THEN** 结构正确，n = line 不在 for-else 中

### Requirement: try-for-if-break-BoolOp 模式正确反编译
系统 SHALL 正确反编译 `try: for item in items: if item is not None and item < 0: break; a = item; except IndexError: a = None` 模式：
- BoolOp `and` 条件不被拆分为两个独立 if
- `a = item` 作为循环体语句（非 else 分支）
- 不生成多余的 `else: return None`

#### Scenario: n13a try_for_if_break_a_indexerror
- **WHEN** 反编译含 BoolOp 条件的 try-for-if-break
- **THEN** 字节码指令数匹配（29 vs 29，非 29 vs 28）

#### Scenario: n13n try_for_if_break_n_valueerror
- **WHEN** 反编译含 isinstance+isdigit BoolOp 条件的 try-for-if-break
- **THEN** 字节码指令数匹配

### Requirement: while-if-try-except 模式正确反编译
系统 SHALL 正确反编译 `while cond: if cond2: try: stmt; except: stmt; i += 1` 模式：
- `i = 0` 初始化语句不丢失
- `i += 1` 后不生成多余的条件判断和 break
- while 条件中 BoolOp 链完整

#### Scenario: n15 while_if_try_except_a_b_indexerror
- **WHEN** 反编译含 while+if+try-except 的嵌套模式
- **THEN** 字节码指令数匹配（54 vs 54，非 54 vs 60）

## MODIFIED Requirements
（无修改需求）

## REMOVED Requirements
（无移除需求）

## 失败测试详细分析

### 测试1: n07 — try_for_break_n_stopiteration
- **期望**: `if v is None: break; n = v`
- **实际**: `if v: n = v; else: break; else: return None`
- **根因**: (1) `v is None` 条件被反转 (2) `n = v` 被放入 if-then 而非循环体 (3) 多余 `else: return None`
- **字节码差异**: 26 vs 25（少1条指令）

### 测试2: n09 — while_try_except_a_indexerror
- **期望**: `try: a = data.pop(); except IndexError: a = None; break`
- **实际**: 正确的 try-except + 多余 `len(data)` 语句
- **根因**: try-except 后的循环条件检查块被当作普通语句生成
- **字节码差异**: 35 vs 40（多5条指令）

### 测试3-4: n10a/n10n — for_if_for_break
- **期望**: `if len(row) > 0: for val in row: ...; a = row`
- **实际**: 内层 for 不在 if 内，`a = row` 在 for-else 中，多余 `if len(row) > 0: pass`
- **根因**: (1) IfRegion 未正确包含内层 LoopRegion (2) for-else 与循环后语句混淆 (3) 重复生成 if 条件
- **字节码差异**: 操作码不匹配（LOAD_GLOBAL vs LOAD_FAST）

### 测试5-6: n13a/n13n — try_for_if_break_BoolOp
- **期望**: `if item is not None and item < 0: break; a = item`
- **实际**: BoolOp 拆分为两个 if，`a = item` 在 else 中，多余 `else: return None`
- **根因**: (1) BoolOp 条件被拆分 (2) 循环后语句放入 else (3) 多余 return None
- **字节码差异**: 29 vs 28（少1条指令）

### 测试7: n15 — while_if_try_except
- **期望**: `i = 0; while ...: if ...: try: ...; except: ...; i += 1`
- **实际**: 缺少 `i = 0`，`i += 1` 后多余 `if i < len(data): pass; else: break`
- **根因**: (1) 循环前语句丢失 (2) 循环回边条件被误生成为 if-else
- **字节码差异**: 54 vs 60（多6条指令）
