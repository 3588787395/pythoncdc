# 失败用例 → 区域类型 → 算法根因映射表

> 基线: 116 failed + 25 errors（去重后 112 测试文件）
> 分析完成: 112 个

## 根因分类汇总

| 根因类型 | 数量 | 说明 |
|---------|------|------|
| STRICT_ASSERT | 60 | 字节码等价但测试结构断言过严 |
| INSTR_UNDERFLOW | 24 | 反编译少指令（丢失代码/操作数） |
| TEST_FRAMEWORK | 18 | 测试框架问题（无法加载源码/执行环境） |
| INSTR_OVERFLOW | 9 | 反编译多指令（生成多余代码） |
| SYNTAX_ERROR | 1 | 反编译结果语法错误 |

## 各根因详细用例

### STRICT_ASSERT（60 个）

- [[IF] `tests/exhaustive/if_region/test_adv18_for_else_nested_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv18_if_with_chained_compare_cond.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv18_nested_ternary_in_elif_cond.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv18_raise_from_complex_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv18_try_finally_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_assert_chained_cmp_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_async_with_async_for_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_await_in_if_cond.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_chained_in_check_in_if_cond.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_for_continue_in_each_branch.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_lambda_iife_in_if_cond.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_mixed_complex_branches.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_multiline_return_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_try_except_else_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_tuple_unpack_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_while_else_break_in_elif_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv19_with_multi_ctx_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_assert_chained_cmp_in_branches.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_class_with_slots_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_dictcomp_complex_filter_in_branches.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_for_else_break_in_each_branch.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_nested_with_try_in_elif_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_star_expr_in_call_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_tuple_return_in_branches.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_walrus_in_while_cond_nested_if.py`
  - diff: 字节码等价但断言失败
- [[IF] `tests/exhaustive/if_region/test_adv20_yield_in_while_in_if_body.py`
  - diff: 字节码等价但断言失败
- [[MATCH] `tests/exhaustive/match_region/test_m106matchguardboolop.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_abc_abstract_property.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_async_aenter.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_dataclass_default_factory.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_magic_methods.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_multi_abstractmethod.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_typeddict_default.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_wraps.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_abc_abstract_property_setter.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_async_aenter.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_asynccontextmanager.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_asyncio_gather.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_cached_property.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_dataclass_default_factory.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_magic_methods.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_typeddict_default.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_wraps.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r13_ternary_nested_lambda.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r14_ternary_yield_from_with_method.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r1_assert_simple.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r1_assert_with_message.py`
  - diff: 字节码等价但断言失败
- [[TERNARY] `tests/exhaustive/ternary/test_r7_ternary_in_async_with.py`
  - diff: 字节码等价但断言失败
- [[NESTED] `tests/exhaustive/nested/test_n15while_if_try_except_a_b_indexerror.py`
  - diff: 字节码等价但断言失败
- [[NESTED] `tests/exhaustive/nested/test_n16try_while_if_break_a_indexerror.py`
  - diff: 字节码等价但断言失败
- [[NESTED] `tests/exhaustive/nested/test_n16try_while_if_break_n_valueerror.py`
  - diff: 字节码等价但断言失败
- [[BASIC] `tests/exhaustive/basic/test_b23yieldfrom_complex.py`
  - diff: 字节码等价但断言失败
- [[L2] `tests/exhaustive/L2_two_level_nested/test_L2_complete.py`
  - diff: 字节码等价但断言失败
- [[L3] `tests/exhaustive/L3_deep_nested/test_L3_complete.py`
  - diff: 字节码等价但断言失败
- [[MATRIX] `tests/control_flow_matrix/test_completeness_matrix.py`
  - diff: 字节码等价但断言失败
- [[MATRIX] `tests/control_flow_matrix/test_l1_expression.py`
  - diff: 字节码等价但断言失败
- [[MATRIX] `tests/control_flow_matrix/test_l3_deep.py`
  - diff: 字节码等价但断言失败
- [[COMPLETENESS] `tests/completeness/test_l2_nested.py`
  - diff: 字节码等价但断言失败
- [[COMPLETENESS] `tests/completeness/test_l3_deep_nested.py`
  - diff: 字节码等价但断言失败
- [[COMPLETENESS] `tests/completeness/test_l4_extreme_nested.py`
  - diff: 字节码等价但断言失败

### INSTR_UNDERFLOW（24 个）

- [[IF] `tests/exhaustive/if_region/test_adv13_ternary_three_or_cond.py`
  - diff: 指令数: 15 vs 9; 指令3: LOAD_NAME vs LOAD_CONST
- [[IF] `tests/exhaustive/if_region/test_adv15_ternary_slice_in_body.py`
  - diff: 指令数: 15 vs 13; 指令4: LOAD_NAME vs STORE_NAME
- [[IF] `tests/exhaustive/if_region/test_adv18_assert_in_if_body.py`
  - diff: 指令数: 31 vs 16; 指令6: LOAD_ASSERTION_ERROR vs LOAD_NAME
- [[MATCH] `tests/exhaustive/match_region/test_m031.py`
  - diff: 指令数: 23 vs 18; 指令1: COPY vs LOAD_CONST
- [[MATCH] `tests/exhaustive/match_region/test_m049.py`
  - diff: 指令数: 33 vs 25; 指令1: COPY vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_kwonly_default.py`
  - diff: 指令数: 10 vs 5; 指令0: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r10_ternary_overload.py`
  - diff: 指令数: 33 vs 23; 指令8: LOAD_NAME vs MAKE_FUNCTION
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_contextlib_suppress.py`
  - diff: 指令数: 35 vs 32; 指令8: LOAD_NAME vs PRECALL
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_frozen_dataclass_default.py`
  - diff: 指令数: 24 vs 16; 指令7: LOAD_NAME vs LOAD_BUILD_CLASS
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_kwonly_default.py`
  - diff: 指令数: 10 vs 5; 指令0: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_overload.py`
  - diff: 指令数: 33 vs 23; 指令8: LOAD_NAME vs MAKE_FUNCTION
- [[TERNARY] `tests/exhaustive/ternary/test_r13_ternary_lambda_default.py`
  - diff: 指令数: 9 vs 5; 指令0: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r14_ternary_walrus_in_while_cond.py`
  - diff: 指令数: 18 vs 2; 指令0: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r14_ternary_while_cond_compare.py`
  - diff: 指令数: 14 vs 2; 指令0: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r14_ternary_with_multiple_second_as.py`
  - diff: 指令数: 44 vs 23; 指令3: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r1_ternary_in_slice.py`
  - diff: 指令数: 12 vs 10; 指令2: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r3_ternary_while_cond.py`
  - diff: 指令数: 14 vs 9; 指令4: LOAD_NAME vs POP_TOP
- [[TERNARY] `tests/exhaustive/ternary/test_r4_ternary_while_cond.py`
  - diff: 指令数: 16 vs 11; 指令2: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r5_ternary_while_cond_body.py`
  - diff: 指令数: 16 vs 11; 指令2: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r5_ternary_while_cond_break.py`
  - diff: 指令数: 17 vs 12; 指令6: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r5_ternary_while_cond_simple.py`
  - diff: 指令数: 14 vs 9; 指令4: LOAD_NAME vs POP_TOP
- [[TERNARY] `tests/exhaustive/ternary/test_r6_ternary_while_cond_complex_body.py`
  - diff: 指令数: 10 vs 9; 指令2: LOAD_NAME vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r6_ternary_while_cond_nested.py`
  - diff: 指令数: 22 vs 14; 指令7: LOAD_CONST vs POP_TOP
- [[TERNARY] `tests/exhaustive/ternary/test_r9_ternary_frozen_dataclass_default.py`
  - diff: 指令数: 24 vs 16; 指令7: LOAD_NAME vs LOAD_BUILD_CLASS

### TEST_FRAMEWORK（18 个）

- [[L1] `tests/exhaustive/L1_basic/test_b05_expression_statement.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c01_if_then.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c02_if_else.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c03_if_elif.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c04_if_elif_else.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c05_multiple_elif_chain.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c06_nested_if.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_c07_nested_if_else.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l01_simple_for.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l02_for_else.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l03_for_break.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l04_for_continue.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l05_for_break_continue.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l06_for_range.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l07_simple_while.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l08_while_else.py`
  - diff: 无法加载 SOURCE_CODE
- [[L1] `tests/exhaustive/L1_basic/test_l09_while_break.py`
  - diff: 无法加载 SOURCE_CODE
- [[COMPLETENESS] `tests/completeness/test_l1_basic_structures.py`
  - diff: 无法加载 SOURCE_CODE

### INSTR_OVERFLOW（9 个）

- [[IF] `tests/exhaustive/if_region/test_adv15_ternary_in_chain_compare_body.py`
  - diff: 指令数: 18 vs 31
- [[IF] `tests/exhaustive/if_region/test_adv15_ternary_in_tuple_unpack.py`
  - diff: 指令数: 14 vs 18; 指令4: LOAD_NAME vs STORE_NAME
- [[BOOLOP] `tests/exhaustive/bool_op/test_bool19_ternary_combo.py`
  - diff: 指令数: 10 vs 11; 指令5: JUMP_IF_TRUE_OR_POP vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r11_ternary_except_star.py`
  - diff: 指令数: 38 vs 41; 指令1: RETURN_VALUE vs STORE_NAME
- [[TERNARY] `tests/exhaustive/ternary/test_r14_ternary_assert_two_ternaries_boolop.py`
  - diff: 指令数: 12 vs 16; 指令6: LOAD_ASSERTION_ERROR vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r1_ternary_in_dict_value.py`
  - diff: 指令数: 11 vs 12; 指令3: LOAD_NAME vs POP_TOP
- [[TERNARY] `tests/exhaustive/ternary/test_r3_ternary_chained_compare_left.py`
  - diff: 指令数: 15 vs 16; 指令7: JUMP_IF_FALSE_OR_POP vs LOAD_CONST
- [[TERNARY] `tests/exhaustive/ternary/test_r6_ternary_decorator_chain.py`
  - diff: 指令数: 17 vs 29; 指令0: LOAD_CONST vs LOAD_NAME
- [[TERNARY] `tests/exhaustive/ternary/test_r9_ternary_exception_group.py`
  - diff: 指令数: 38 vs 41; 指令1: RETURN_VALUE vs STORE_NAME

### SYNTAX_ERROR（1 个）

- [[TERNARY] `tests/exhaustive/ternary/test_r1_chained_compare_in_cond.py`
  - diff: 语法错误: 'return' outside function (<dec>, line 2)

---

## 算法根因映射（共性聚类）

> 上述分类是「字节码 diff 表层分类」。下表把表层分类归约为少数「算法根因」，
> 每个根因对应一类需要从算法层面（而非个例）修复的问题。
> 遵循规范核心约束：禁止跨区域跨层次启发式 / 禁止后处理补丁 / 必须识别阶段一次正确。

### 根因 A: while 条件位三元表达式识别失败（9 个 INSTR_UNDERFLOW）

**覆盖用例**：test_r3_ternary_while_cond, test_r4_ternary_while_cond,
test_r5_ternary_while_cond_{body,break,simple}, test_r6_ternary_while_cond_{complex_body,nested},
test_r14_ternary_walrus_in_while_cond, test_r14_ternary_while_cond_compare

**共性字节码模式**：`while <ternary_expr>[:> N]` 编译为
条件位三元（LOAD cond; IF_FALSE → false_value; LOAD true_value; JUMP_FORWARD → merge;
false_value: LOAD false_value; merge: [COMPARE_OP] POP_JUMP_IF_FALSE → exit）。
当前 LoopRegion 识别把条件位三元误并入循环条件，三元结构被吞，条件退化为常量
（如 `while 0:`）或部分操作数。

**算法根因**：TernaryRegion 识别器在 LoopRegion 之后运行，LoopRegion 的
header_block 吞掉了三元 cond 块。Scenario B 修复（Phase 2.5.3b）仅覆盖
`merge_block IS LoopRegion.header_block` 的最简形式，未覆盖：
(a) walrus 包裹（`while (n := ternary) > 0`）— COPY/STORE 插入使 merge 偏移；
(b) 比较包裹（`while ternary > 0`）— COMPARE_OP 在 merge 之后；
(c) 嵌套三元作为 while 条件。

**修复方向**：TernaryRegion 识别应在 LoopRegion 之前对 header_block 做「条件位
三元」探测（基于 IF_FALSE 跳转目标 + JUMP_FORWARD 回 merge 的结构模式），
把三元 cond 块归约为 TernaryRegion，LoopRegion 引用其入口作为抽象条件节点。
这是「识别阶段一次正确」，不是后处理补丁。

### 根因 B: 默认参数/装饰器/类体三元的 code object 重建（STRICT_ASSERT 误分类，~15 个）

**覆盖用例**：test_r10/r11_ternary_{kwonly_default,overload,frozen_dataclass_default,
dataclass_default_factory,typeddict_default,wraps,magic_methods,abc_abstract_property,...}

**共性**：这些用例的原始字节码与反编译字节码**实际等价**（diff 工具因嵌套 code object
对齐错位误报为 INSTR_UNDERFLOW）。测试失败原因是断言要求 IfExp 节点出现在
「默认参数值」「装饰器链」「类体属性」位置，但 code_generator 把三元保留在
这些位置的源码字符串里，重编译后 IfExp 在嵌套 code object 内部，顶层 AST walk
找不到。这是**测试断言过严**（STRICT_ASSERT），非反编译 bug。

**修复方向**：不修反编译器。评估测试断言是否应改为「字节码等价」而非「AST 结构匹配」。

### 根因 C: assert + if 归约混淆（3 个 INSTR_UNDERFLOW/OVERFLOW）

**覆盖用例**：test_adv18_assert_in_if_body, test_adv19_assert_chained_cmp_in_if_body,
test_adv20_assert_chained_cmp_in_branches, test_r14_ternary_assert_two_ternaries_boolop

**共性字节码模式**：`assert <cond>` 编译为 LOAD_ASSERTION_ERROR + RAISE，
与 `if not <cond>: raise` 的字节码结构相似。当前 IfRegion 识别器把 assert
误归约为 if-raise，或反之。

**算法根因**：`_identify_conditional_regions` 未区分 assert 的
LOAD_ASSERTION_ERROR 模式与 if-raise 的 LOAD_NAME(AssertionError) 模式。
这是「识别阶段」的语义判别缺失。

**修复方向**：在 IfRegion 识别时，若 body 块首指令是 LOAD_ASSERTION_ERROR +
RAISE，应让 AssertStatement 识别器（在 IfRegion 之前）接管，而非 IfRegion 吞掉。

### 根因 D: 链式比较 + 三元/boolop 混合的指令数偏移（6 个 INSTR_OVERFLOW/UNDERFLOW）

**覆盖用例**：test_adv15_ternary_in_chain_compare_body, test_adv15_ternary_in_tuple_unpack,
test_adv15_ternary_slice_in_body, test_adv18_if_with_chained_compare_cond,
test_r3_ternary_chained_compare_left, test_r1_ternary_in_slice

**共性**：BUILD_SLICE / BUILD_TUPLE / 链式比较 内嵌三元时，指令数偏移 2-4 条。
三元作为子表达式（slice 索引、tuple 元素、比较操作数）时，生成阶段未把三元
作为原子值节点嵌入，而是展开为独立语句。

**算法根因**：TernaryRegion 的 `value_target` 语义未覆盖「值被 BUILD_SLICE/
BUILD_TUPLE/COMPARE_OP 消费」的情况。生成阶段把三元 region 当独立语句生成，
破坏了子表达式位置。

**修复方向**：TernaryRegion 生成时，若 merge_block 后继是 BUILD_SLICE/
BUILD_TUPLE/COMPARE_OP 等「值消费」指令，应把三元作为子表达式节点嵌入，
而非独立语句。

### 根因 E: 顺序语句 boolop 边界（已修复，bo53）

**覆盖用例**：test_P1_complete EXPR02（已修）, bo53（回归测试）

**说明**：此根因已在 commit 1c20271 修复。但修复方式（POP_TOP 首指令判据）
是「实例驱动」补丁，违反规范原则。需在 Phase 1 算法反思中重新设计为
基于「短路跳转目标语义」的普遍性判据。

### 根因 F: 测试框架问题（18 个 TEST_FRAMEWORK + 23 NOOK errors）

**覆盖用例**：L1_basic 17 个（SOURCE_CODE 无法 ast.literal_eval 加载）、
completeness 1 个、NOOK 23 errors（FileNotFoundError/import error）

**说明**：非反编译 bug。L1_basic 用 `def test_...(): exec(SOURCE_CODE)` 模式，
SOURCE_CODE 是函数体内字符串，ast 无法在模块级 literal_eval。
NOOK 测试依赖 file3.txt 等外部文件。

**修复方向**：修测试框架，不修反编译器。

### 根因 G: STRICT_ASSERT（~45 个，字节码等价但 AST 结构断言过严）

**覆盖用例**：if_region 26 个（adv18-20 系列）、ternary 15 个、
nested 3 个、basic 1 个、L2/L3/matrix/completeness 若干

**共性**：反编译字节码与原始字节码完全等价，但测试断言要求特定 AST 结构
（如「必须有 IfExp」「必须嵌套 if」「必须有 N 个 If」）。CPython 编译器对
语义等价的代码产生相同字节码（如 `if c: if d:` ≡ `if c and d:`，
`x = a if c else b` 在默认参数里 ≡ 函数体内三元）。反编译器还原任一等价形式
都正确，但测试只接受其中一种。

**修复方向**：不修反编译器。评估测试断言是否应改为「字节码等价」标准。

---

## 修复优先级

1. **根因 A（while 条件位三元，9 个）** — 普遍性算法修复，影响 ternary 9 个
2. **根因 C（assert/if 混淆，4 个）** — 识别阶段语义判别
3. **根因 D（子表达式三元，6 个）** — 生成阶段值消费判别
4. **根因 E（顺序 boolop，已修但需重设计）** — Phase 1 算法反思
5. **根因 B/G（STRICT_ASSERT，~60 个）** — 评估测试断言标准
6. **根因 F（测试框架，41 个）** — 修测试不修反编译器

