# 修复22个反编译测试失败 Spec

## Why
当前基线 52f/1846p (97.3%)，其中 try_except 8f、ternary 7f、match_region 7f 共22个失败测试需要修复，以提升反编译器对嵌套结构和子表达式的处理能力。

## What Changes
- **region_ast_generator.py**: 修复 `_generate_try_body` 父区域误识别、`_generate_handler_body_statements` SWAP/POP_EXCEPT处理、`_generate_match` case body生成、`_generate_ternary` 子表达式嵌入、`_generate_if`/`_generate_loop` ternary条件提取
- **region_analyzer.py**: 修复 `_mr_collect_case_body` or-guard收集、`_collect_guard_pattern_blocks` allowed集合、嵌套TryExceptRegion识别
- **BREAKING**: 无破坏性变更

## Impact
- Affected specs: fix-try-except-failures, fix-boolop-ternary-failures, fix-with-match-region-failures
- Affected code: region_ast_generator.py (主要), region_analyzer.py (次要)

## ADDED Requirements

### Requirement: Match case body中嵌套try-except正确生成
当match case body包含try-except时，`_generate_try_body`应找到嵌套TryExceptRegion而非父MatchRegion。

#### Scenario: M054/M061/M069 try在match case body中
- **WHEN** match case body包含try-except结构
- **THEN** 反编译输出应包含完整的try-except，try body不应为pass

### Requirement: Match guard with BoolOp正确处理
or-guard (`case n if n >= 100 or n < -10`) 的case body应正确收集和生成。

#### Scenario: M106 or-guard case body
- **WHEN** match case有or-guard条件
- **THEN** case body应包含实际语句（如`return "small"`），不应为pass

### Requirement: Match guard表达式不泄漏到case body
guard中的比较/调用表达式不应出现在case body中。

#### Scenario: M083 guard表达式泄漏
- **WHEN** match case有`if len(lst) > 0`guard
- **THEN** `len(lst) > 0`不应作为独立语句出现在case body中

### Requirement: Handler body return语句正确合并
except handler中`LOAD_X; SWAP; POP_EXCEPT; RETURN_VALUE`模式应生成`return expr`而非`expr; return`。

#### Scenario: TRY15 handler return
- **WHEN** except handler包含`return default`
- **THEN** 反编译输出应为`return default`而非`default\nreturn`

### Requirement: Ternary作为子表达式嵌入上下文
ternary表达式应能嵌入函数参数、if条件、while条件、for迭代器、lambda体等上下文。

#### Scenario: TE04 ternary作为函数参数
- **WHEN** 函数调用参数包含ternary表达式
- **THEN** ternary应嵌入Call节点参数中，而非作为独立表达式语句

#### Scenario: ternary11 ternary在if条件中
- **WHEN** if条件包含ternary表达式如`if (a if c else b) > threshold`
- **THEN** ternary应嵌入if条件中

#### Scenario: ternary12 ternary在while条件中
- **WHEN** while条件包含ternary表达式
- **THEN** ternary应嵌入while条件中

#### Scenario: ternary13 ternary在for迭代器中
- **WHEN** for迭代器包含ternary表达式
- **THEN** ternary应嵌入for的iter中，不应产生语法错误

#### Scenario: ternary17 ternary在lambda中
- **WHEN** lambda体包含ternary表达式
- **THEN** lambda体应为ternary表达式

#### Scenario: ternary20 复杂ternary嵌套
- **WHEN** elif分支包含ternary表达式
- **THEN** ternary应嵌入return语句中

## MODIFIED Requirements

### Requirement: 嵌套try-except识别与生成
嵌套try-except（handler body包含内层try、try-finally中finally包含try等）应正确识别和生成。

#### Scenario: TE080/TRY16 handler body中嵌套try
- **WHEN** except handler body包含内层try-except
- **THEN** 应正确生成嵌套try-except结构，而非pass

#### Scenario: TE081 finally中嵌套try
- **WHEN** try-finally的finally块包含try-except
- **THEN** finally块应包含完整的try-except结构

#### Scenario: TE100 三层嵌套try
- **WHEN** 三层嵌套try-except
- **THEN** 每层handler body应包含正确语句，不重复

#### Scenario: TE104 try-except-finally
- **WHEN** try-except-finally中handler有return
- **THEN** finally内容不应泄漏到try body，handler body应包含return

## REMOVED Requirements
无移除的需求。
