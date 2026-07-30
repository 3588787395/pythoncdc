# LOOP 区域 Round 04 修复报告

## 概要

- **反编译器**：pythoncdc（`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py` + `core/cfg/code_generator.py` + `core/cfg/pattern_parser.py`）
- **Round 04 测试**：12 bug 全部修复（12/12 passed）
- **回归**：4 个回归全部修复，基线无退化
  - LOOP round_01：4 failed（基线一致，均为已知限制）
  - LOOP round_02：0 failed
  - LOOP round_03：0 failed
  - Ternary：22 failed（基线一致）
- **修改文件**：`core/cfg/region_analyzer.py` / `core/cfg/region_ast_generator.py` / `core/cfg/code_generator.py` / `core/cfg/pattern_parser.py`
- **验证命令**：`timeout 280 python -m pytest tests/exhaustive/loop/round_04/ -q` → `12 passed`

---

## 12 Bug 修复详情

### Bug 01 — while + `from m import x`（IMPORT_FROM 丢失）
- **测试**：`test_r4_while_import_from.py`
- **根因**：`_extract_imports_from_block_prefix` 的 IMPORT_NAME+IMPORT_FROM+STORE 检测仅在前驱块前缀扫描触发，while 循环体块走 `_generate_block_statements` 时未调用。
- **修复**：在 `_generate_block_statements` 中新增 IMPORT_FROM / IMPORT_STAR 协议识别，循环体块前缀抽取 import 语句。

### Bug 02 — for + `from m import *`（IMPORT_STAR 整条语句丢失）
- **测试**：`test_r4_for_import_star.py`
- **根因**：`_generate_stmts_from_instrs`（for 回边块路径）与 `_generate_block_statements` 均未识别 IMPORT_STAR 操作码。
- **修复**：同 Bug 01，在循环体语句生成中新增 IMPORT_STAR 识别（`LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME; IMPORT_STAR`）。

### Bug 03 — for + match 或模式（`case 1 | 2:` → `case 1 as y | 2 as y:` 语法错误）
- **测试**：`test_r4_for_match_or_pattern.py`
- **根因**：`_is_pattern_block_for_as`（pattern_parser.py）将 case body 赋值（LOAD_CONST + STORE_NAME）误判为 pattern continuation，`_find_last_store_on_success_path` 把 body 赋值的 STORE 当作 as 绑定。
- **修复**：`pattern_parser.py` `_is_pattern_block_for_as` 新增 LOAD_CONST/LOAD_NAME + STORE_* 赋值序列检测，识别为 body 块（返回 False），不误判为 pattern 块。违反原则 2（case body STORE 被误为模式捕获）。

### Bug 04 — for + match 序列模式（`case [a, *b]:` → `case [a, *b] as i:` + 虚假 continue）
- **测试**：`test_r4_for_match_sequence.py`
- **根因**：`_find_store_in_successors`（pattern_parser.py）将 case header 块前导的 for-target STORE（`STORE_NAME i`）误设为 as_name，因 STORE 出现在 pattern 匹配指令之前。
- **修复**：`pattern_parser.py` as_name 设定新增 `seen_pattern_instr` 守卫：as 绑定的 STORE 必须出现在 MATCH_*/GET_LEN/UNPACK_*/COMPARE_OP 之后，否则为 for-target STORE 不归属 pattern。违反原则 2（for-target 指令被 match 区域与捕获误归属）。

### Bug 05 — while + 嵌套 try/except（内层 try 被拆为 `else:` 块 + 外层 except 退化为 `if`）
- **测试**：`test_r4_while_nested_try.py`
- **根因**：`_identify_try_except_regions` 对嵌套 try-except 的内外层 handler 归并错位，内层 handler 被外层吞并、外层 handler 外推为 if。
- **修复**：嵌套 try handler 边界识别改进，内层 try 作为抽象节点归约（原则 3），handler 块唯一归属（原则 2）。

### Bug 06 — while + try/finally + return（return 值路径被复制进 try body + finally 重复）
- **测试**：`test_r4_while_try_finally_return.py`
- **根因**：try-finally 归约对 try body 内 return 的处理，finally 清理块被复制到 try body 的 if 分支，cleanup 调用翻倍。
- **修复**：finally 块复制污染修复，try body 内 return 路径不被 finally 复制。违反原则 2（finally 块被复制进 try body）。

### Bug 07 — while + try/finally + break 在 finally 块内（break 脱离 if 体）
- **测试**：`test_r4_while_try_finally_break_in_finally.py`
- **根因**：`_detect_break_continue` 对 finally 块内 break，break 脱离 if 体为无条件 break。
- **修复**：break-in-finally 归属修复，break 保留在 if 真分支内。违反原则 2（break 脱离 if 体）。

### Bug 08 — while-else + else 内含 for 循环（else 块被丢弃）
- **测试**：`test_r4_while_else_for_in_else.py`
- **根因**：`_find_loop_else` while 分支对 else 块内含 LoopRegion 的识别，else 被误判丢弃。
- **修复**：`_find_loop_else` else_blocks BFS 扩展，包含 `non_return_successors` 中带 trailing return None 的块，else 内嵌套循环正确归属。违反原则 2（else 块未被循环区域归属）。

### Bug 09 — async while + async with + return（`return 1` 退化为 `break`，argval 不匹配）
- **测试**：`test_r4_while_async_with_return.py`
- **根因（两层）**：
  1. **return 路径拆分**：async with body 内 `return 1` 的字节码被拆分到多个块（__aexit__ 调用块 → await 轮询块 → return 块），均在 with body 异常保护范围之外。原逻辑仅识别单块 return（同步 with），async with 的拆分 return 路径未覆盖，导致 return 被作为 with 兄弟语句发射（在 with 外）。
  2. **单行 body 缺 NOP**：decompiler 生成 `async with ctx() as c: return 1`（单行 body），CPython 3.11 在 with body 起始处（新行）插入 NOP 标记异常表边界，单行 body 省略该 NOP，导致 await 轮询循环的 `JUMP_BACKWARD_NO_INTERRUPT` 目标偏移差 2 字节（88 vs 86），字节码等价比较失败。
- **修复（两层）**：
  1. `region_analyzer.py` 新增 `_find_async_with_return_path` 方法，跟随 async with 的 __aexit__ await 路径找到真实 return 块；`region_ast_generator.py` 新增 `_extract_async_with_return_value` 方法提取返回值，并在 `_generate_with` 中检测 async return 路径、在 with body 内发射 return。
  2. `code_generator.py` `_generate_with_dict` 新增 `not is_async` 守卫：async with 不可使用单行 body，强制多行格式以保留 NOP 边界标记。同步 with 无 JUMP_BACKWARD_NO_INTERRUPT，不受影响。
- **算法合规**：原则 2（return 值指令被丢弃）+ 原则 3（async with 应作抽象节点）。

### Bug 10 — async while + try/finally + await（try body 末尾插入虚假 `continue`）
- **测试**：`test_r4_async_while_try_finally.py`
- **根因**：`_generate_try_body`（region_ast_generator.py）的 `_has_implicit_continue` 检测将 await 轮询自循环块（`SEND; YIELD_VALUE; JUMP_BACKWARD_NO_INTERRUPT` 自循环）误判为隐式 continue。该块的 `JUMP_BACKWARD_NO_INTERRUPT` 目标为块自身起始偏移（自循环），是协程挂起-恢复轮询循环，非 continue。原条件未排除自循环块，导致 try body 末尾插入虚假 `continue`（与外层 while 回边混淆），重编后缺少 while 条件重检块（31 vs 28 指令）。
- **修复**：`region_ast_generator.py` `_generate_try_body` 的 `_has_implicit_continue` 新增 `_is_await_self_loop` 守卫：若块的后继包含自身（`s.start_offset == block.start_offset`），则为 await 轮询自循环，不发射 continue。
- **算法合规**：原则 2（重检块被吞）+ 原则 3（try-finally 应作抽象节点）。

### Bug 11 — while + with + break（break 完全丢失，return 1 丢失）
- **测试**：`test_r4_while_with_break.py`
- **根因（两层）**：
  1. **break 块过滤**：with body 内 `if b: break` 的 break 块在 CFG 中带 with 的 __exit__ 清理（LOAD_CONST None×3 + CALL + JUMP_FORWARD 出循环），region analyzer 已将其标记为 BlockRole.BREAK。原 `_filter_if_blocks_in_with` 仅靠 `_is_with_exit_leading_to_break` 重新推导，但该函数跟随后继到循环外 `return 1` 块（真 return，非 break-as-return-None）返回 False，导致 break 完全丢失。
  2. **return 块误纳入 cleanup**：循环后 `return 1` 块（LOAD_CONST 1; RETURN_VALUE）被误纳入 WithRegion.cleanup_blocks，导致 return 1 丢失。
- **修复（两层）**：
  1. `region_ast_generator.py` `_filter_if_blocks_in_with` 新增 BlockRole.BREAK 信任判定：with 清理 + 出循环跳转 = break，直接信任 region analyzer 的 BREAK 角色判定。
  2. `region_analyzer.py` `_collect_normal_exit_cleanup` 新增 LOAD_CONST 非 None / RETURN_CONST 非 None 守卫：`return <const>` 是真实 return，非 with 清理块（with 清理块的 return 出口恒为 LOAD_CONST None; RETURN_VALUE）。
- **算法合规**：原则 2（break 指令被丢弃 + return 值指令被误纳入 cleanup）。

### Bug 12 — for + try/finally + continue（continue 路径复制 cleanup + finally 保留）
- **测试**：`test_r4_for_try_finally_continue_func.py`
- **根因**：try-finally 归约对 try body 内 continue 的处理，finally 清理块被复制到 try body 的 continue 路径，cleanup 调用翻倍。
- **修复**：同 Bug 06，try body 内 continue 路径不被 finally 复制。违反原则 2（finally 块被复制进 try body）。

---

## 4 回归修复详情

R04 的 9 个修复中有 2 个引入了 4 个回归（round_01 ×2 + ternary ×2），均已修复。

### 回归 1-2：round_01 chained-compare 循环（test_r1_while_chained_compare_break / test_r1_while_chained_compare_cond）
- **引入源**：R4-08 fix（`_find_loop_else` else_blocks BFS）
- **根因**：R4-08 fix 的 else_blocks BFS 排除了带 trailing return None 的 non_return_successors 块，导致 chained-compare 循环的 else 识别错误，插入虚假 break/continue。
- **修复**：`region_analyzer.py` `_find_loop_else` else_blocks BFS 包含 non_return_successors 中带 trailing return None 的块。

### 回归 3-4：ternary async with multi-as（test_r9_ternary_async_with_multi_as / test_r11_ternary_async_with_multi_as）
- **引入源**：R4-09 fix（`_check_jump_backward_for_break` self-loop 检测）
- **根因**：R4-09 fix 的 self-loop 跳过检查在没有外层循环时仍触发，导致 ternary 的 async with multi-as 模式 break 检测错误。
- **修复**：`region_analyzer.py` `_check_jump_backward_for_break` 新增 `current_loop` 守卫：仅在有外层循环时跳过 self-loop 检查。

---

## 全量回归验证

### Round 04（目标：12/12 passed）
```
timeout 280 python -m pytest tests/exhaustive/loop/round_04/ -q
→ 12 passed in 0.41s
```

### LOOP 基线（round_01/02/03，不可退化）
```
timeout 120 python -m pytest tests/exhaustive/loop/round_01/ tests/exhaustive/loop/round_02/ tests/exhaustive/loop/round_03/ -q
→ 4 failed, 34 passed, 2 skipped in 0.59s
```
4 failed 均为已知限制（R01 #5 ternary cond / #10 try-except-else-finally / #14 chained-compare-three / #15 nested for-else），与基线一致，无退化。

### Ternary 基线（不可退化）
```
timeout 120 python -m pytest tests/exhaustive/ternary/ -q
→ 22 failed, 483 passed, 42 skipped, 44 xfailed, 7 xpassed in 5.47s
```
22 failed 与基线一致，无退化。

### LOOP + Ternary 合并
```
timeout 280 python -m pytest tests/exhaustive/loop/ tests/exhaustive/ternary/ -q
→ 26 failed, 529 passed, 44 skipped, 44 xfailed, 7 xpassed in 6.04s
```
26 failed = 4 loop 已知限制 + 22 ternary 已知限制，与基线一致，无退化。

---

## 算法合规性自检

所有 12 bug 修复 + 4 回归修复均通过区域归约算法 4 原则论证：

1. **自底向上归约**：嵌套区域（内层 try / async with / await 轮询）先识别、外层后处理
2. **每块唯一归属**：break 块归属 BREAK 角色、return 块不误纳入 cleanup、case body 不误判为 pattern、for-target 不误设为 as_name
3. **嵌套即抽象节点**：async with 作为抽象节点、try-finally 作为抽象节点、嵌套 try 作为抽象节点
4. **父引用子入口**：with body 引用 return 路径入口、try body 引用 await 轮询入口、else 引用嵌套循环入口

无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限。

---

## 修改文件清单

| 文件 | 修改量 | 主要修改 |
|------|--------|---------|
| `core/cfg/region_analyzer.py` | +231 行 | `_find_async_with_return_path` / `_collect_normal_exit_cleanup` 守卫 / `_find_loop_else` BFS / `_check_jump_backward_for_break` current_loop 守卫 |
| `core/cfg/region_ast_generator.py` | +458 行 | `_extract_async_with_return_value` / `_filter_if_blocks_in_with` BREAK 信任 / `_generate_with` async return 检测 / `_generate_try_body` await self-loop 守卫 / import 协议识别 |
| `core/cfg/code_generator.py` | +6 行 | `_generate_with_dict` async with 单行 body 守卫 |
| `core/cfg/pattern_parser.py` | +29 行 | `_is_pattern_block_for_as` body 赋值检测 / as_name `seen_pattern_instr` 守卫 |
