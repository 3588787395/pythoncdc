# 区域归约算法完善反编译 - 全面迭代 Spec

## Why

当前反编译器在 site-packages 的 402 个 pyc 文件中，355 个已 OK（88.3%），47 个仍 partial。156 个函数字节码不一致，主要根因：try/except 区域内嵌套结构识别不完整、for/while 循环与 try 交互错位、for-else/while-else break 检测缺陷、chained compare BoolOp 生成错误、ternary 表达式在 with 上下文中丢失前缀语句。需要严格按区域归约算法修复，逐个 pyc 达到字节码完全匹配，最终 402/402 全部 OK。

## What Changes

- 修复 try/except 区域内嵌套 if/for/while 的归约边界计算
- 修复 for-else/while-else 中 break 检测与 else 块生成
- 修复 chained compare 中 BoolOp 分离逻辑
- 修复 ternary 表达式在 with 上下文中前缀语句丢失
- 修复 POP_JUMP_FORWARD_IF_TRUE 条件反转时的跳转目标
- 修复 elif 链中异常表范围与 then/else 块不匹配
- 修复 with 语句内 return/continue 导致的块截断
- 每轮修复后更新 pyc_index.json 并生成 OK.py 文件
- 每轮 commit + push（前缀 `spr-rNN:`）
- **BREAKING**: 任何修复必须符合区域归约算法 4 原则，禁止 `_fix_`/`_patch_`/`_merge_` 等反模式

## Impact

- Affected specs: 所有 prior specs（`region-algorithm-perfect-decompile`, `site-packages-full-decompile-10rounds` 等）
- Affected code: `core/cfg/region_analyzer.py`（区域识别）, `core/cfg/region_ast_generator.py`（AST 生成）, `pycdc.py`（入口）
- Algorithm compliance: FULLY COMPLIANT（区域归约 4 原则）

## ADDED Requirements

### Requirement: 逐个 pyc 字节码完全匹配验证

系统 SHALL 逐个反编译 partial pyc 文件，对比反编译产物重编译后的字节码与原 pyc 字节码，要求每个函数 co_code 完全一致。

#### Scenario: 单个 pyc 修复闭环
- **WHEN** 一个 partial pyc 被修复后
- **THEN** 反编译产物重编译后字节码与原 pyc 的每个函数 co_code 完全匹配
- **AND** 在同目录下生成同名 + OK 的 .py 文件
- **AND** pyc_index.json 中该文件 bytecode_match_rate 更新为 1.0、decompile_status 更新为 "ok"

### Requirement: 双工程师迭代流程

每轮 SHALL 由测试工程师和修复工程师协作完成：

#### Scenario: 测试工程师职责
- **WHEN** 取一个 partial pyc 文件
- **THEN** 反编译并逐函数字节码 diff
- **AND** 提取 >=10 个最小复现实例（.py 文件，compile → 反编译 → diff 不一致）
- **AND** 归类不一致的根因（区域类型 + 算法偏离点）

#### Scenario: 修复工程师职责
- **WHEN** 收到测试工程师的分析结果
- **THEN** 按区域归约算法 4 原则修复 `region_analyzer.py` 或 `region_ast_generator.py`
- **AND** 所有 10+ 最小复现实例通过
- **AND** 目标 pyc 字节码完全匹配
- **AND** quotation.pyc 回归验证通过
- **AND** 全量已 OK 的 pyc 回归无退化

### Requirement: 每轮至少修复一个 pyc

每轮 SHALL 至少将一个 partial pyc 转为 OK（字节码完全匹配），否则禁止进入下一轮。

#### Scenario: 轮次推进条件
- **WHEN** 某轮修复完成
- **THEN** 至少一个 partial pyc 的 decompile_status 变为 "ok"
- **AND** 已 commit + push 到 origin/main
- **AND** 下一轮方可开始

### Requirement: 批量回归验证

每轮修复后 SHALL 使用 `scripts/pyc_batch_verify.py` 进行批量回归验证。

#### Scenario: 回归验证无退化
- **WHEN** 修复工程师完成修复
- **THEN** 执行 `python scripts/pyc_batch_verify.py batch --round N` 验证全量 pyc
- **AND** 已 OK 的 pyc 不出现退化（bytecode_match_rate 不下降）

### Requirement: OK.py 生成与 pyc_index.json 更新

每轮修复后 SHALL 在 pyc 同目录生成同名+OK 的 .py 文件并更新索引。

#### Scenario: 文件生成
- **WHEN** 一个 pyc 字节码完全匹配
- **THEN** 在 pyc 同目录下生成 `<name>OK.py` 文件
- **AND** pyc_index.json 中该条目 bytecode_match_rate=1.0, decompile_status="ok"

### Requirement: 每轮 commit + push

每轮完成后 SHALL commit + push 到 origin/main，commit 前缀 `spr-rNN:`。

#### Scenario: 提交
- **WHEN** 一轮所有验证通过
- **THEN** git add 相关文件 + git commit -m "spr-rNN: <summary>" + git push
- **AND** 不提交反编译生成的 OK.py 文件（这些由验证脚本自动生成）

### Requirement: 禁止修改反编译生成的文件

系统 SHALL NOT 修改反编译生成的 OK.py 文件，只修改反编译器源码。

#### Scenario: 只改源码
- **WHEN** 修复反编译问题
- **THEN** 只修改 `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py` 等源码
- **AND** 不修改任何 `*OK.py` 文件

## MODIFIED Requirements

### Requirement: 区域归约算法 4 原则

1. 从最内层到最外层识别区域（归约顺序）
2. 每个块在任何层级只属于一个区域
3. 嵌套区域在其父区域中作为单个抽象节点表示
4. 归约后父区域的 then/else 列表引用子区域的入口，而不是子区域的所有块

## REMOVED Requirements

(none)
