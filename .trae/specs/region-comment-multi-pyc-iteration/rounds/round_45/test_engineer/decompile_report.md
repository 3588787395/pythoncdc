# R45 测试工程师反编译报告

## 目标 pyc 文件
- `site-packages/IQCommon/api/klinedata.pyc`（按 path 字母序第一个 not-ok）
- 批量分析 top 30 partial pyc 文件

## 当前 pyc 状态
- decompile_status: partial
- total_functions: 45
- matched_functions: 18
- match_rate: 40.00%
- mismatches: 27

## 累计成功率
- total_pyc: 402
- ok_pyc: 232
- partial_pyc: 170
- failed_pyc: 0
- total_functions: 6617
- matched_functions: 5762
- cumulative_match_rate: 87.08%

## 失败模式分析（top 30 partial pyc）

### Top 失败模式（first_diff 统计）
| 模式 | 次数 |
|------|------|
| PUSH_EXC_INFO -> RETURN_VALUE | 18 |
| LOAD_GLOBAL -> LOAD_FAST | 13 |
| ? -> LOAD_CONST | 11 |
| LOAD_CONST -> LOAD_CONST (0 vs None) | 11 |
| SWAP -> POP_TOP | 8 |
| LOAD_CONST -> LOAD_GLOBAL (None vs slice) | 7 |
| GET_ITER -> POP_TOP | 6 |
| LOAD_METHOD -> LOAD_CONST | 5 |
| LOAD_GLOBAL -> LOAD_CONST | 5 |

### Top opcode 转换模式
| 模式 | 次数 |
|------|------|
| LOAD_GLOBAL -> LOAD_FAST | 64 |
| LOAD_FAST -> LOAD_GLOBAL | 42 |
| LOAD_FAST -> LOAD_FAST | 42 |
| LOAD_CONST -> LOAD_CONST | 39 |
| LOAD_CONST -> LOAD_FAST | 32 |
| LOAD_FAST -> LOAD_CONST | 31 |
| LOAD_METHOD -> LOAD_FAST | 22 |
| LOAD_GLOBAL -> LOAD_CONST | 22 |
| LOAD_ATTR -> LOAD_FAST | 21 |
| PUSH_EXC_INFO -> RETURN_VALUE | 19 |

## 最小复现实例

### 12 个复现实例已归档至 `minimal_repros/`

| 编号 | 名称 | 状态 | 说明 |
|------|------|------|------|
| repro_01 | try_except_return | DEFECT-REPRO → NO-DEFECT (修复后) | except handler return 值丢失 |
| repro_02 | try_except_finally | DEFECT-REPRO | finally 块代码泄漏到 except 块 |
| repro_03 | try_except_continue | NO-DEFECT | 控制组 |
| repro_04 | slice_none | NO-DEFECT | 控制组 |
| repro_05 | slice_complex | NO-DEFECT | 控制组 |
| repro_06 | tuple_swap | NO-DEFECT | 控制组 |
| repro_07 | swap_conditional | NO-DEFECT | 控制组 |
| repro_08 | for_else | NO-DEFECT | 控制组 |
| repro_09 | nested_try_for | NO-DEFECT | 控制组 |
| repro_10 | with_try | NO-DEFECT | 控制组 |
| repro_11 | chained_method | NO-DEFECT | 控制组 |
| repro_12 | if_elif_method | NO-DEFECT | 控制组 |

## 根因分析

### repro_01: except handler return 值丢失
- **根因**: `_generate_handler_body_statements` 方法中，POP_EXCEPT 后的 skip_offsets 循环无条件跳过所有 LOAD_CONST 指令，包括 as-var 清理链之后的 return 值表达式
- **影响**: `return 0` 变成 `return None`，except handler 体丢失
- **修复方向**: 仅跳过 as-var 清理链（3 条指令）+ RETURN_VALUE，不跳过中间的 return 值表达式

### repro_02: try-except-finally 块顺序错乱
- **根因**: finally 块的 cleanup 代码被错误插入到 except handler 中
- **影响**: except handler 中出现重复的 finally 代码
- **修复方向**: 需要进一步分析 finally 块的代码生成逻辑
