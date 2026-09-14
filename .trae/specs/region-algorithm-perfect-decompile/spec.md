# 区域归约算法完善反编译 Spec

## Why

当前反编译器在 site-packages 的 402 个 pyc 文件中，344 个已 OK（85.6%），58 个仍 partial。317 个函数的字节码不一致，主要根因：try/except 区域内嵌套结构识别不完整（150 例）、for/while 循环与 try 交互错位（166 例）、async 函数内语句丢失（7 例）、EXTENDED_ARG 前缀跳转目标计算错误、以及 elif/else 块边界与异常表范围不匹配。需要严格按区域归约算法修复，逐个 pyc 达到字节码完全匹配。

## What Changes

- 修复 try/except 区域内嵌套 if/for/while 的归约边界计算
- 修复 EXTENDED_ARG 指令对跳转目标偏移的影响
- 修复 async 函数（RETURN_GENERATOR + GET_AWAITABLE）内语句丢失
- 修复 POP_JUMP_FORWARD_IF_TRUE 与 IF_TRUE 条件反转时的跳转目标计算
- 修复 elif 链中异常表范围与 then/else 块不匹配
- 修复 with 语句内 return/continue 导致的块截断
- 每轮修复后更新 pyc_index.json 并生成 OK.py 文件
- 每轮 commit + push（前缀 `spr-rNN:`）
- **BREAKING**: 任何修复必须符合区域归约算法 4 原则，禁止 `_fix_`/`_patch_`/`_merge_` 等反模式

## Impact

- Affected specs: 所有 prior specs（`site-packages-full-decompile-10rounds`, `site-packages-pyc-perfect-10rounds`, `region-comment-multi-pyc-iteration`）
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
- **THEN** 至少一个 pyc 的 bytecode_match_rate 从 <1.0 变为 1.0
- **AND** commit + push 到 origin/main（前缀 `spr-rNN:`）

### Requirement: 10 轮迭代上限

SHALL 执行最多 10 轮迭代，每轮创建独立文件夹归档（`rounds/round_NN/`）。

#### Scenario: 迭代终止
- **WHEN** 10 轮完成或所有 58 个 partial pyc 全部 OK
- **THEN** 迭代终止
- **AND** 最终成功率 >= 100%（已 OK 的不退化 + 新修复的）

### Requirement: 核心失败模式修复

系统 SHALL 修复以下已识别的失败模式（按优先级）：

1. **try/except 内嵌套结构边界**（150 例）: try 块内含 if/for/while 时，归约将子区域块错误归入 except handler
2. **for/while 循环与 try 交互**（166 例）: 循环体内 try 的异常表范围覆盖了循环条件块
3. **recomp_shorter**（153 例）: 反编译产物缺少语句（如 async 函数内调用丢失、elif 分支丢失）
4. **recomp_longer**（103 例）: 反编译产物多余语句（如 try/except 外多出 None 赋值、重复 return）
5. **same_length_diff**（47 例）: 字节数相同但跳转目标偏移错误（如 EXTENDED_ARG 影响、条件反转错误）
6. **async 函数语句丢失**（7 例）: RETURN_GENERATOR 函数内语句未被生成
7. **missing_func**（14 例）: 反编译产物缺少函数定义

#### Scenario: try/except 嵌套边界修复
- **WHEN** try 块内包含 if/for/while 子区域
- **THEN** 归约后父区域的 then_blocks 只引用子区域入口，不包含子区域的所有块
- **AND** except handler 的边界不覆盖 try 体内的子区域块

### Requirement: 禁止修改反编译生成的文件

禁止修改已生成的 OK.py 文件。如需重新生成，应先删除再反编译。

#### Scenario: OK.py 文件保护
- **WHEN** 反编译生成 OK.py 文件后
- **THEN** 后续任何修复不得修改该文件
- **AND** 如需更新，必须先删除再重新反编译生成

## MODIFIED Requirements

### Requirement: 区域识别方法注释

所有 `_identify_*_regions` 方法的 docstring SHALL 包含 6 节：区域类型 / 算法描述 / 字节码模式 / 边界条件 / 归约语义 / AST映射+已知失败模式。修复工程师每次修改方法时 SHALL 同步更新注释。

## REMOVED Requirements

无移除需求。
