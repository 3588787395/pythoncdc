# R45 修复工程师报告

## 修复概述

### Pattern: except handler return 值丢失（repro_01）

**缺陷描述**: 在 `_generate_handler_body_statements` 方法中，当 except handler 包含 `return <value>` 语句时，POP_EXCEPT 后的 skip_offsets 循环会无条件跳过所有 LOAD_CONST/STORE_FAST/DELETE_FAST 指令。这导致 as-var 清理链（LOAD_CONST None + STORE_FAST + DELETE_FAST）之后的 return 值表达式（如 `LOAD_CONST 0`）也被错误跳过，使 `return 0` 变成 `return None`。

**触发条件**: except handler 使用 `except Exception as e: return <value>` 模式，其中 return 值表达式在 as-var 清理链之后。

**修复点**: `core/cfg/region_ast_generator.py` `_generate_handler_body_statements` 方法

**修复内容**:
1. 新增 `elif _has_return_after_cleanup and not stmt_instrs:` 分支：当 return 值表达式在 as-var 清理链之后时（stmt_instrs 为空），收集清理链和 RETURN_VALUE 之间的指令作为 return 值表达式，重建 Return 语句
2. 修改 skip_offsets 循环：仅跳过 as-var 清理链（r0, r1, r2）+ RETURN_VALUE，不跳过中间的 return 值表达式指令

**算法依据**:
- 原则 2（每块唯一归属）：return 值表达式归 Return 语句，as-var 清理归 except 机制框架
- 非补丁：修复基于指令的结构模式识别，无硬编码 offset / 无跨区域启发式

## 注释更新清单
- `_generate_handler_body_statements` 方法内 `[R45 fix]` 行内注释已追加（2 处）
  1. 新增 elif 分支注释：说明 return 值在 as-var 清理后的收集逻辑
  2. 修改 skip_offsets 循环注释：说明仅跳过清理链 + RETURN_VALUE

## 回归测试结果
- 12 个最小复现实例：11/12 NO-DEFECT, 1 DEFECT-REPRO（repro_02，独立缺陷）
- `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- 批量验证 20 个 partial pyc：无回归（87.08% 不变）

## 残留不一致
- klinedata.pyc 仍 40%（27 mismatches），主要模式为 PUSH_EXC_INFO 结构重建、LOAD_GLOBAL->LOAD_FAST 变量作用域
- repro_02 try-except-finally 块顺序错乱（独立缺陷，后续轮次修复）
- 跨轮残留 Pattern 不变
