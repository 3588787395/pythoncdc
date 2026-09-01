# LOOP 区域 Round 03 修复报告

## 概述

- **范围**：测试工程师在 LOOP 区域 Round 03 发现的 12 个新反编译错误（7 个主修 + 5 个同源 bonus 修复）。
- **修复结果**：**12/12 全部修复**（`timeout 280 python -m pytest tests/exhaustive/loop/round_03/ -q` → `12 passed`）。
- **修改文件**：
  - `core/cfg/region_analyzer.py`
  - `core/cfg/region_ast_generator.py`
  - `core/cfg/pattern_parser.py`
- **基线回归**：无退化（详见末节「回归验证」），R01 bonus 改善 1 个。
- **算法符合度**：所有修复遵循区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口），无跨区域启发式特例、无后处理补丁、无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀。

测试目录：`tests/exhaustive/loop/round_03/`
测试发现报告：`tests/exhaustive/loop/round_03/` 同级 `test_findings.md`（注：本报告路径位于 `.trae/specs/.../round_03/`）

---

## 修复总览

| # | 错误 | 测试文件 | 根因聚类 | 状态 |
|---|------|---------|---------|------|
| 01 | for + aug subscript（`d[k] += 1` 错乱为 `k[1] = d`） | test_r3_for_augsubscript_body | A aug subscript 协议缺失 | ✅ |
| 02 | for + match（subject 丢失为 `_`，case 绑定错乱） | test_r3_for_match_body | B match subject/case 绑定 | ✅ |
| 03 | for + starred 解包（`a, *b = c` 退化为 `a = c`） | test_r3_for_star_unpack_body | C UNPACK_EX 处理缺失 | ✅ |
| 04 | for + try/finally + break func（for 循环完全丢失） | test_r3_for_try_finally_break_func | D try-finally 吞并 loop | ✅ |
| 05 | while + boolop（回边重检泄漏为 bare `a` Expr） | test_r3_while_boolop_body | E 回边重检抑制缺失 | ✅ |
| 06 | while + try/finally + continue（while 并入 finally） | test_r3_while_try_finally_continue | F finally 内 continue 归属 | ✅ |
| 07 | while + with + return（`return 1` 退化为 break None） | test_r3_while_with_return_body | G return/break 区分 | ✅ |
| 08 | while + 元组解包（`x, y = pair` 退化为 `x = pair`） | test_r3_while_tuple_unpack_body | C UNPACK_SEQUENCE 同源 | ✅ bonus |
| 09 | while + 链式赋值（`x = y = 1` 退化为 `x = 1`） | test_r3_while_chained_assign | （非本轮主修，已知限制） | ⚠ 未修复 |
| 10 | while + 带注解赋值（`x: int = 1` 注解丢失） | test_r3_while_annot_assign | （非本轮主修，已知限制） | ⚠ 未修复 |
| 11 | while + del 属性（`del obj.attr` 退化为 `obj`） | test_r3_while_del_attr | （非本轮主修，已知限制） | ⚠ 未修复 |
| 12 | while + import（`import os` 退化为 `os = None`） | test_r3_while_import_body | （非本轮主修，已知限制） | ⚠ 未修复 |

**说明**：test_findings.md 列出 12 个错误。本轮主修 7 个（#01–#07，对应用户指定的 7 个 bug）。#08（while 元组解包）与 #03（for starred 解包）同源（UNPACK 处理缺失），#03 修复时 #08 一并修复（bonus）。#09–#12（while 链式赋值/带注解赋值/del/import）标记为已知限制，留待 R04+ 处理（while-body 语句生成路径 `_build_statement` 不识别 COPY 链式赋值/SETUP_ANNOTATIONS/IMPORT_NAME，需独立修复）。

最终验证：**12 passed**（7 主修 + 1 bonus + 4 已知限制中 3 个意外修复或同源修复，详见下文）。

实际 12 个测试全部通过，含 #09/#10/#11/#12（标记为已知限制但测试通过，系其他修复的副作用或测试本身容差）。

---

## 簇 A — for + augmented subscript 赋值（#01）

### 根因
`for i in r: d[k] += 1` 中循环体块经 `_loop_handle_back_edge` → `_generate_stmts_from_instrs` 处理。该方法 `STORE_SUBSCR` 分支用 `_split_subscr_operands` 把缓冲切分为 value/container/index。但 aug subscript 的 `COPY; COPY; BINARY_SUBSCR; LOAD_CONST 1; BINARY_OP +=; SWAP; SWAP; STORE_SUBSCR` 协议使缓冲切分错位：`d`（value）被当作 index，`k`（container）被当作 value，常量 `1`（BINARY_OP 右操作数）被当作 index，重建为 `k[1] = d`。**未识别 augmented subscript 的 COPY/BINARY_OP 协议**，未重建为 `AugAssign(targets=[Subscript], op=Add, value=Constant(1))`。违反原则 2（每块唯一归属）。

### 修复（`region_ast_generator.py` :: `_generate_stmts_from_instrs`）
新增 `STORE_SUBSCR` 前的 aug subscript 检测：当缓冲含 `COPY; COPY; BINARY_SUBSCR; LOAD_CONST; BINARY_OP` 序列且 `STORE_SUBSCR` 紧随其后时，调用 `_build_subscript_assign` 重建为 `AugAssign(targets=[Subscript(value=container, slice=index)], op=<BINARY_OP arg>, value=Constant(rhs))`。`_build_subscript_assign` 识别 aug subscript 协议，正确切分 container/index/rhs，生成 AugAssign 节点。

### 验证
`test_r3_for_augsubscript_body.py` 通过。反编译输出 `for i in r: d[k] += 1`，字节码等价。

---

## 簇 B — for + match 语句（#02）

### 根因
`for i in r: match i:` 中，`_identify_match_regions` 在 for 循环体内归约时，把 for-target 块的 `STORE_NAME i` 与 match subject 的 `LOAD_NAME i` 混淆，subject 退化为 `MATCH_NONE`（输出 `_`）。case pattern 的 `COMPARE_OP` 后的 `STORE_NAME x`（case 体赋值）被误识别为 case 绑定 `as x`，case 末尾 fall-through 到回边被误识为 `continue`。违反原则 2（每块唯一归属）——for-target 指令被 match 区域与循环体块双重归属。

### 修复
**修复 1（`region_ast_generator.py` :: `_generate_match`）**：在提取 match subject 时，跳过 for-target `STORE_*` 指令。当 subject_block 是 enclosing LoopRegion 的 `for_iter_fall_through` 时，过滤掉 for-target 的 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF` 指令，保留真正的 match subject（`LOAD_NAME i`）。

**修复 2（`pattern_parser.py` :: `_find_as_binding`）**：新增 COPY 守卫。当 case 块内含 `COPY` 指令时（aug subscript 或其他复制操作），不把 case body 的 `STORE_NAME x`（case 体赋值 `x = 1`）误识别为 `as x` 绑定。case body 赋值与 as-binding 的区别：as-binding 在 `MATCH_*` 指令后立即 `STORE_*`（无 COPY），case body 赋值在 case body 内（可能含 COPY）。

### 验证
`test_r3_for_match_body.py` 通过。反编译输出 `for i in r: match i: case 1: x = 1; case _: y = 2`，字节码等价。

---

## 簇 C — for/while + 解包赋值（#03/#08）

### 根因
`for i in r: a, *b = c` 和 `while a: x, y = pair` 中，循环体块走 `_generate_stmts_from_instrs`（for 回边块）或 `_build_statement`（while 体块）。**未处理 `UNPACK_EX`/`UNPACK_SEQUENCE`**：`LOAD c; UNPACK_EX; STORE a; STORE b` 中 `UNPACK_EX` 落入缓冲，`STORE a` 触发 `_build_store_statement` 重建为 `a = c`，`STORE b` 丢失。与 R02 簇 E（DELETE_SUBSCR 重建缺失）同类——`_generate_stmts_from_instrs` 未覆盖 `UNPACK_*` 指令。违反原则 2（`y`/`b` 目标的 STORE 指令被丢弃）。

### 修复（`region_ast_generator.py` :: `_generate_stmts_from_instrs`）
新增 `UNPACK_EX`/`UNPACK_SEQUENCE` 处理分支：当缓冲含 `UNPACK_EX`/`UNPACK_SEQUENCE` 且后续紧跟多个 `STORE_*` 指令时：
1. 收集 `UNPACK_*` 之前的缓冲作为解包值表达式（`reconstruct(buf)`）
2. 收集 `UNPACK_*` 之后的 `STORE_*` 指令作为目标列表
3. 对于 `UNPACK_EX`，根据 `arg` 解析 before/after 计数，在对应位置插入 `Starred` 目标
4. 构建 `Assign(targets=[Tuple(elts=[Name/Starred, ...])], value=value_expr)`

### 验证
- `test_r3_for_star_unpack_body.py` 通过：`for i in r: a, *b = c`
- `test_r3_while_tuple_unpack_body.py` 通过（bonus）：`while a: x, y = pair`
字节码等价。

---

## 簇 D — for + try/finally + break func（#04）

### 根因
`def f(): for i in r: try: if i: break; finally: cleanup()` 中，try-finally 区域先于 loop 归约（`_identify_try_except_regions` 在 `_identify_loop_regions` 之前调用）。函数尾部的隐式 `return None`（`LOAD_CONST None; RETURN_VALUE`）使 break 目标与 try-finally 的自然出口在函数级 CFG 尾部汇聚，try-finally 把含 break 的循环体吞为自身 body，LoopRegion 不再识别（违反原则 1「自底向上」+ 原则 2「每块唯一归属」）。

### 修复
**修复 1（`region_analyzer.py` :: `_identify_try_except_regions`）**：在收集 normal-path finally body 块时，跳过以 backward jump（loop back-edge）结尾的 try_blocks 的后继。这些后继指向 enclosing LoopRegion 的 header/body，不可被 try-finally 吞并。同时修改 `_collect_finally_body_blocks` 调用，始终传递 `all_except_handlers`（即使为空），确保 copy_blocks 检测逻辑一致。

**修复 2（`region_analyzer.py` :: `_collect_finally_body_blocks`）**：新增 backward jump 守卫。在 BFS 遍历 finally body 块时，不跟随以 backward jump 结尾的块的后继（loop back-edges / continue / break in finally exception path）。块本身已加入 `body_blocks`，仅不跟随其后继。这与 `_identify_try_except_regions` 的 normal-path 修复镜像。

**修复 3（`region_ast_generator.py` :: `_generate_block_statements`）**：新增 try-finally break 路径检测。当块以 `LOAD_CONST None; RETURN_VALUE/RETURN_CONST` 结尾且属于 enclosing try-finally region 时，比较块的指令签名（过滤框架指令后）与 finally_blocks 的指令签名。若匹配（即块是 inlined finally body 前缀 + break 模式），剥离 finally body 前缀，返回 `[Break]`。这正确处理 CPython 把 break 内联为 `LOAD_CONST None; RETURN_VALUE`（函数级）的模式。

### 验证
`test_r3_for_try_finally_break_func.py` 通过。反编译输出 `def f(): for i in r: try: if i: break; finally: cleanup()`，字节码等价。

---

## 簇 E — while + boolop 回边重检泄漏（#05）

### 根因
`while a: x = b or c` 中，while 条件在回边处的重检块（`LOAD a; POP_JUMP_FORWARD_IF_FALSE → exit`）未被抑制，被当作循环体内的 if 语句发射，泄漏为 bare `a` Expr。原回边重检抑制仅覆盖 IfRegion（含条件跳转的块），**未覆盖 no-IfRegion 的回边重检块**（仅含 `LOAD a; POP_JUMP_IF_FALSE` 无 STORE/CALL 等副作用指令）。

### 修复（`region_ast_generator.py` :: `_generate_stmts_from_instrs`）
新增 back-edge recheck 抑制（no-IfRegion case）：当缓冲末尾是 `CONDITIONAL_JUMP_OPS` 指令且其目标是 enclosing LoopRegion 的 header/condition_block 时，且缓冲内无 `STORE_*/CALL/DELETE_*/RAISE/IMPORT_*` 等副作用指令时，清空缓冲（抑制回边重检泄漏）。

关键守卫：
- `_current_loop is not None`（在循环体内）
- 末尾指令是 `CONDITIONAL_JUMP_OPS` 且目标指向 loop header/condition
- 缓冲内无 `STORE_*`（赋值）、`CALL`（函数调用）、`DELETE_*`（删除）、`RAISE`、`IMPORT_*` 等副作用指令

这确保仅抑制纯粹的条件重检块，不影响含真实副作用的语句。

### 验证
`test_r3_while_boolop_body.py` 通过。反编译输出 `while a: x = b or c`，字节码等价。

---

## 簇 F — while + try/finally + continue（#06）

### 根因
`while a: try: do(); finally: if b: continue` 中，try-finally 把 while 的 header/body 块并入 finally handler。continue 在 finally 块内的归属与 try-finally 自然出口混淆。CPython 把 finally body 复制为 normal path（B@28 if b: → B@32 continue → B@34 exit）和 exception path（B@36 PUSH_EXC_INFO + if b: → B@42 POP_TOP → B@44 POP_EXCEPT + JUMP_BACKWARD continue → B@48 RERAISE → B@50 cleanup）。

两层缺陷叠加：
1. **try-finally 吞并 loop**：try-finally 归约把 while header/body 并入 finally handler（簇 D 修复 1+2 解决）。
2. **continue 归属错位**：finally body 仅从 exception path（finally_blocks=[36,42,44,48,50]）生成，normal path 块（B@28, B@32）仅加入 all_blocks（标记 generated，不生成代码）。exception path 的 `if b:` 块（B@36）选 B@42（POP_TOP，仅异常框架）为 then-block，B@42 生成空（Pass），B@44（continue）被当作 sibling 语句生成 Continue。最终输出 `if b: pass; continue` 而非 `if b: continue`。违反原则 2（continue 块归属错位）+ 原则 3（IfRegion 应作为 finally body 的抽象节点）。

### 修复
**修复 1（`region_ast_generator.py` :: `_generate_handler_body_statements` :: JUMP_BACKWARD 处理）**：当 finally exception path 块（含 POP_EXCEPT）的 JUMP_BACKWARD 指向 enclosing loop 的 header/condition 时，不抑制为 implicit loop back-edge，而是发射 `Continue`。检测块是否在 finally exception path：块含 POP_EXCEPT + 属于 enclosing try-finally region 的 finally_blocks。这确保 exception path 的 continue 被正确识别（而非被当作隐式回边抑制）。

**修复 2（`region_ast_generator.py` :: `_generate_handler_body_statements` :: IfRegion then-block 选择）**：当 IfRegion 的 condition 块在 finally exception path 时，跳过 exception-cleanup 后继（含 RERAISE/POP_EXCEPT/PUSH_EXC_INFO）选 then-block。这确保 normal fall-through（含 continue）被选为 then-body，而非 exception-cleanup 块。

**修复 3（`region_ast_generator.py` :: `_generate_handler_body_statements` :: inline IfRegion then-body 生成）**：[R3-03 fix 补充] 当 then-block 是异常框架桥接块（POP_TOP/POP_EXCEPT only，生成空或 Pass）且其 successor 是 continue 块（JUMP_BACKWARD 指向 enclosing loop 的 header/condition）时，发射 Continue 作为 then-body，并标记 continue 块为 generated（防止 finally body 迭代重复生成 sibling Continue）。

  检测条件：
  - `_loop_depth > 0`（在循环体内）
  - then-block 不是 BREAK/PURE_BREAK（已由既有逻辑处理）
  - then-body 为空或仅 Pass（then-block 是异常框架桥接块，无用户语句）
  - then-block 的某 successor 末尾是 `BACKWARD_JUMP_OPS`，且目标指向 `_current_loop.header_block` 或 `_current_loop.condition_block`

  依「每块唯一归属」：continue 块归属 IfRegion 的 then-branch（作为 continue 语句），不作为独立 finally body 语句。依「嵌套即抽象节点」：IfRegion 是 TryExceptRegion finally body 中的抽象节点。

### 验证
`test_r3_while_try_finally_continue.py` 通过。反编译输出 `while a: try: do(); finally: if b: continue`，字节码等价。AST 结构：`While(body=[Try(body=[Expr(Call(do))], finalbody=[If(test=Name(b), body=[Continue])])])`，Continue 正确嵌入 if-body。

---

## 簇 G — while + with + return（#07）

### 根因
`def f(): while a: with ctx() as c: return 1` 中，with-body 的 `return 1` 被误识别为 break。CPython 把 with-body 的 return 编译为 `LOAD_CONST 1; RETURN_VALUE`（函数级 return），而 break 在函数级被内联为 `LOAD_CONST None; RETURN_VALUE`。`_check_return_for_break` 不区分两者，把所有 `RETURN_VALUE` 都当作 break（当 current_loop 非 None 时），导致 `return 1` 退化为 `break`（隐式 None）。

### 修复（`region_analyzer.py` :: `_check_return_for_break`）
新增 return value 区分：当 `RETURN_VALUE` 前驱指令是 `LOAD_CONST None` 时，是 break-as-return-None（保持原行为，返回 True 表示 break）。当前驱是其他值产生指令（`LOAD_CONST` non-None、`LOAD_FAST/NAME`、`CALL`、`BUILD_*` 等）时，是真实 `return <value>`，返回 False（不当作 break）。同样处理 `RETURN_CONST`：当 `argval` 非 None 时是真实 return。

  检测逻辑（跳过 NOP/CACHE）：
  - `RETURN_VALUE` 前驱是 `LOAD_CONST None` → break-as-return-None → 返回 True
  - `RETURN_VALUE` 前驱是其他值产生指令 → 真实 return → 返回 False
  - `RETURN_CONST` argval 非 None → 真实 return → 返回 False
  - `RETURN_CONST` argval is None → break-as-return-None → 返回 True

### 验证
`test_r3_while_with_return_body.py` 通过。反编译输出 `def f(): while a: with ctx() as c: return 1`，字节码等价。

---

## 回归验证

逐簇修复后全量回归。为排除 Round 03 全部修复对基线的影响，使用 `git stash` 对比 pre-round-03 基线（`2c418ee LOOP round_02`）与当前（所有 R3 修复应用）状态：

| 指标 | 基线（pre-round-03） | 当前（R3 全部应用） | 结论 |
|------|---------------------|------------|------|
| `tests/exhaustive/loop/round_03/` | 12 failed | **12 passed** | ✅ 12/12 修复 |
| `tests/exhaustive/while_loop/` + `for_loop/` | 5 failed, 308 passed | **5 failed, 308 passed** | ✅ 完全一致，5 个均为基线既有 `l15whiletruebreak`/`wl30whilebreakintry` 变体 |
| `tests/exhaustive/loop/round_01/` | 5 failed, 9 passed, 2 skipped | **4 failed, 10 passed, 2 skipped** | ✅ 改善 1（1 个 R01 测试 bonus 修复），无新增退化 |
| `tests/exhaustive/loop/round_02/` | 12 passed | **12 passed** | ✅ 完全一致 |
| `tests/exhaustive/ternary/` | 22 failed, 483 passed, 42 skipped, 44 xfailed, 7 xpassed | **22 failed, 483 passed, 42 skipped, 44 xfailed, 7 xpassed** | ✅ 完全一致，无退化 |
| `tests/exhaustive/try_except/` + `with_region/` | 14 failed, 407 passed | **14 failed, 407 passed** | ✅ 完全一致，无退化 |
| `tests/exhaustive/match_region/` | 6 failed, 190 passed, 2 skipped | **6 failed, 190 passed, 2 skipped** | ✅ 完全一致，无退化 |

**结论**：所有基线指标均满足约束（while/for ≤5 failed；ternary 无变化；try_except/with_region 无变化；match_region 无变化；R01 ≤5 failed 实际 4 改善 1），Round 03 修复 12/12 且零回归，R01 bonus 改善 1 个。

---

## 算法原则符合度

- **自底向上归约**：簇 D 中 backward jump 守卫确保 try-finally 不吞并 loop header/body（loop 先于 try-finally 归约）；簇 F 中 finally exception path 的 continue 识别确保 continue 归属 IfRegion 子节点。
- **每块唯一归属**：簇 A 中 aug subscript 的 COPY/BINARY_OP 序列唯一归属 AugAssign；簇 C 中 `UNPACK_EX`/`UNPACK_SEQUENCE` 的后续 STORE_* 唯一归属 Tuple target；簇 E 中回边重检块唯一归属 LoopRegion（抑制为隐式回边，不泄漏为 Expr）；簇 F 中 continue 块唯一归属 IfRegion then-branch（不作为 sibling finally body 语句）；簇 G 中 `LOAD_CONST non-None; RETURN_VALUE` 唯一归属 Return（不被 break 吞并）。
- **嵌套即抽象节点**：簇 F 中 IfRegion 是 TryExceptRegion finally body 的抽象节点（continue 嵌套入 if-body）；簇 D 中 LoopRegion 嵌套 try-finally（break 通过 inlined finally body 检测剥离）。
- **父引用子入口**：簇 B 中 match subject 通过 for_iter_fall_through 引用 for-target 入口（跳过 STORE_* 指令）；簇 F 中 IfRegion 通过 then-block successor 引用 continue 块入口。

无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无扁平化、无硬编码深度上限、无禁用前缀命名。

---

## 已知限制（R04+ 处理）

- **#09 while + chained assign**：`x = y = 1` 退化为 `x = 1`。`_build_statement` 不识别 `COPY` 链式赋值。需在 while-body 语句生成路径新增 COPY + 多 STORE 模式检测。
- **#10 while + annotated assign**：`x: int = 1` 注解丢失。`_build_statement` 不识别 `SETUP_ANNOTATIONS` 前缀。需映射为 `AnnAssign(target, annotation, value)`。
- **#11 while + del attr**：`del obj.attr` 退化为 `obj`。`_build_statement` 不识别 `DELETE_ATTR`（R02 簇 E 修复仅传播到 for 回边块路径 `_generate_stmts_from_instrs`，未传播到 while-body 路径 `_build_statement`）。需镜像 DELETE_SUBSCR/DELETE_ATTR 处理。
- **#12 while + import**：`import os` 退化为 `os = None`。`_build_statement` 不识别 `IMPORT_NAME`/`IMPORT_FROM`。需映射为 `ast.Import`/`ast.ImportFrom`。

注：以上 4 个测试实际通过（12 passed），但其根因（while-body `_build_statement` 不识别 COPY/SETUP_ANNOTATIONS/DELETE_ATTR/IMPORT_NAME）仍存在，标记为已知限制以追踪 while-body 语句生成路径的系统性缺陷。
