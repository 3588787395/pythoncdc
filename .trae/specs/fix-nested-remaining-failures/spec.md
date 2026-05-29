# 修复Nested区域剩余20个失败测试 Spec

## Why
当前nested区域从27f降至20f（第一轮修复后），但存在一个严重的回归bug：`_trailing_return_none_stmts`变量在`_loop_generate_for`方法中未定义但被引用，导致107个额外测试崩溃。修复此bug后，需要继续修复剩余20个失败测试，将nested区域通过率从89.6%提升至接近100%。

## What Changes
- **紧急修复**: 在`_loop_generate_for`中定义`_trailing_return_none_stmts`变量，消除107个崩溃
- **修复1**: BoolOp在If内部短路跳转被错误替换 (nested_if_boolop, 3f)
- **修复2**: With在If内部多余5条指令 (nested_if_with, 3f)
- **修复3**: 内层while break跳转到外层多余13条指令 (n23, 3f)
- **修复4**: 嵌套while-if-while-break内层break归属错误 (n11, 2f)
- **修复5**: try内for循环if break归属错误 (n13, 2f)
- **修复6**: 嵌套for-if-for-break内层break归属错误 (n10, 2f)
- **修复7**: while内try-except多余5条指令/少2条指令 (n09, 2f)
- **修复8**: try内for break差1条指令 (n07, 1f)
- **修复9**: while-if-try-except多余6条指令/少2条指令 (n15, 2f)

## Impact
- Affected code: `core/cfg/region_ast_generator.py` — 核心修改文件（优先）
- Affected code: `core/cfg/region_analyzer.py` — 仅在必要时修改（高风险）
- 测试文件: `tests/exhaustive/nested/` — 20个目标失败测试
- 全量回归: 10个区域测试套件

## ADDED Requirements

### Requirement: 紧急修复 _loop_generate_for 中 _trailing_return_none_stmts 未定义bug
系统 SHALL 在 `_loop_generate_for` 方法中定义 `_trailing_return_none_stmts` 变量，与 `_loop_generate_while` 中的逻辑一致。当for循环的else块只含trailing return None且body含break时，移除else块。

#### Scenario: for循环含break且else块仅含return None
- **WHEN** 反编译含break的for循环且else块仅含`return None`时
- **THEN** else块被正确移除，不产生NameError崩溃

### Requirement: BoolOp在If内部正确生成 (nested_if_boolop)
系统 SHALL 在IfRegion内部正确处理BoolOpRegion子区域，不将短路跳转指令错误替换为STORE_NAME。

#### Scenario: nested_if_boolop
- **WHEN** 反编译 `if a and b: ...` 在嵌套If结构中时
- **THEN** JUMP_IF_FALSE_OR_POP指令正确保留，不被替换为STORE_NAME

### Requirement: With在If内部正确生成 (nested_if_with)
系统 SHALL 在IfRegion内部正确处理WithRegion子区域，不生成多余的5条指令。

#### Scenario: nested_if_with
- **WHEN** 反编译含with语句的if结构时
- **THEN** with body指令数与原始字节码匹配

### Requirement: 内层while break正确归约 (n23)
系统 SHALL 正确识别内层while循环的break语句，不将其与外层while循环条件混淆。

#### Scenario: n23whileinwhilebreak
- **WHEN** 反编译嵌套while循环含break时
- **THEN** break正确归约到内层循环，不产生多余13条指令

### Requirement: 嵌套while-if-while-break内层break归属正确 (n11)
系统 SHALL 正确识别嵌套while-if-while结构中内层while的break语句。

#### Scenario: n11while_if_while_break
- **WHEN** 反编译 `while x < limit: if x % 2 == 0: while y < 10: if y == 5: break` 时
- **THEN** break归属到内层while循环，指令数匹配

### Requirement: try内for循环if break归属正确 (n13)
系统 SHALL 在try-except上下文中正确识别for循环内的if break语句。

#### Scenario: n13try_for_if_break
- **WHEN** 反编译try块内含for循环且for内含if break时
- **THEN** break正确归属到for循环，指令数/操作码匹配

### Requirement: 嵌套for-if-for-break内层break归属正确 (n10)
系统 SHALL 正确识别嵌套for-if-for结构中内层for的break语句。

#### Scenario: n10for_if_for_break
- **WHEN** 反编译嵌套for循环含if break时
- **THEN** break正确归属到内层for循环，操作码/指令数匹配

### Requirement: while内try-except指令数匹配 (n09)
系统 SHALL 在while循环内正确生成try-except结构，不多余5条指令不少2条指令。

#### Scenario: n09while_try_except
- **WHEN** 反编译while循环内含try-except时
- **THEN** 指令数与原始字节码匹配

### Requirement: try内for break差1条指令修复 (n07)
系统 SHALL 在try上下文中正确生成for循环的break语句。

#### Scenario: n07try_for_break
- **WHEN** 反编译try块内含for break时
- **THEN** 指令数与原始字节码匹配（差0条而非差1条）

### Requirement: while-if-try-except指令数匹配 (n15)
系统 SHALL 在while-if嵌套结构中正确生成try-except，不多余6条指令不少2条指令。

#### Scenario: n15while_if_try_except
- **WHEN** 反编译while-if嵌套中含try-except时
- **THEN** 指令数与原始字节码匹配

## MODIFIED Requirements

### Requirement: for循环else块trailing return None处理
`_loop_generate_for` 方法 SHALL 与 `_loop_generate_while` 一致地处理else块中的trailing return None。当else块仅含return None且body含break时，移除else块。

## REMOVED Requirements
（无移除需求）

## 关键约束

1. **优先修改region_ast_generator.py** — region_analyzer.py修改风险极高
2. **每次修改后必须运行全量10区域回归测试** — 确保零回归
3. **如果导致for_loop回归立即回退** — for_loop是红线指标
4. **第一轮已应用的3处修改不可回退**:
   - `_process_if_blocks` 中CONTINUE/PURE_CONTINUE块处理逻辑重排
   - `_loop_generate_while` 中 `has_trailing_return_none` 检查扩展
   - `_stmt_contains_break` 辅助方法

## 当前基线（修复bug前）

| 区域 | 失败 | 通过 | 跳过 | 通过率 |
|------|------|------|------|--------|
| nested | 127f* | 135p | 23s | ~52%* |
| *含107个_trailing_return_none_stmts崩溃 | | | | |

## 修复bug后预期基线

| 区域 | 失败 | 通过 | 跳过 | 通过率 |
|------|------|------|------|--------|
| nested | ~20f | ~232p | ~26s | ~89.6% |
