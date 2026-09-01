# LOOP 区域 Round 02 修复报告

## 概述

- **范围**：测试工程师在 LOOP 区域 Round 02 发现的 12 个新反编译错误（6 类根因，聚类 A–F）。
- **修复结果**：**12/12 全部修复**（`timeout 240 python -m pytest tests/exhaustive/loop/round_02/ -q` → `12 passed`）。
- **修改文件**：
  - `core/cfg/region_analyzer.py`
  - `core/cfg/region_ast_generator.py`
- **基线回归**：无退化（详见末节「回归验证」）。
- **算法符合度**：所有修复遵循区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口），无跨区域启发式特例、无后处理补丁、无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀。

测试目录：`tests/exhaustive/loop/round_02/`
测试发现报告：`tests/exhaustive/loop/round_02/` 同级 `test_findings.md`（注：本报告路径位于 `.trae/specs/.../round_02/`）

---

## 修复总览

| # | 错误 | 测试文件 | 根因聚类 | 状态 |
|---|------|---------|---------|------|
| 01 | for-else+break（模块级）else 丢失 | test_r2_for_else_break_module | A for-else 识别 | ✅ |
| 02 | for-else+break（多语句）else 丢失 | test_r2_for_else_multi_stmt_module | A for-else 识别 | ✅ |
| 03 | for-else（else 含 return 无尾随）else 丢失 | test_r2_for_else_return_no_trailing | A for-else 识别 | ✅ |
| 04 | for-else+continue+break else 丢失+if/elif 合并 | test_r2_for_else_continue_break | A for-else 识别 | ✅ |
| 05 | while+break if/elif 回边重检泄漏 | test_r2_while_break_if_elif | B while 回边重检 | ✅ |
| 06 | while+两顶层 break 回边重检泄漏 | test_r2_while_two_break_top_level | B while 回边重检 | ✅ |
| 07 | while-else+break+continue 回边重检泄漏+else 丢失 | test_r2_while_else_break_continue | B while 回边重检+else | ✅ |
| 08 | while+多嵌套 break 回边重检泄漏+BoolOp 误合并 | test_r2_while_multi_break_nested | B while 回边重检+BoolOp | ✅ |
| 09 | while-True+break+continue break 脱离 if | test_r2_while_true_break_continue_mix | C break 归属 | ✅ |
| 10 | for-iter walrus 双重求值 | test_r2_for_iter_walrus | D for-iter setup 双重归属 | ✅ |
| 11 | for body del 未重建 | test_r2_for_body_del | E DELETE_SUBSCR 重建缺失 | ✅ |
| 12 | while body await 循环退化为 if | test_r2_while_body_await | F await 轮询循环误抑制 | ✅ |

---

## 簇 A — for-else 识别缺陷（#1/#2/#3/#4）

### 根因
`_find_loop_else`（`region_ast_generator.py`）的 for-loop 分支在 break/return/continue 场景下误返 `None`，导致 `else` 子句退化为循环后的顺序语句。模块级场景下 break 目标与 for_iter_exit 都汇入模块尾部的 `LOAD_CONST None; RETURN_VALUE` 块，`_break_hits_for_iter_exit` 判定为真，else_blocks 返回 None。#3 的 else 以 `return` 结束且无尾随语句时，else 块被 `_is_early_return_block` 误判为早返回块而过滤。

### 修复
在 `_detect_break_continue` 中识别 CPython 在模块/函数尾部把 `break` 内联为 `POP_TOP; LOAD_CONST None; RETURN_VALUE` 的模式：当循环存在非平凡 `else_block` 且 return 块是平凡 `return None` 时，将其归类为 break 而非自然返回，从而保留 else 子句归属。新增 `for_iter_exit` / `else_blocks` 参数以区分 break 与自然返回。

### 验证
4 个簇 A 测试通过。

---

## 簇 B — while 回边重检泄漏（#5/#6/#7/#8）

### 根因
while 条件在回边处的重检块（`LOAD a; POP_JUMP_FORWARD_IF_FALSE → exit`）未被抑制，被当作循环体内的 if 语句发射，泄漏为虚假 `elif a: pass / else: break` 分支。常叠加 if-elif 误合并或 else 丢失。

### 修复（`region_analyzer.py`）
1. `_check_elif_chain`：过滤回边重检块（含 BACKWARD 条件跳转的块）出 IfRegion 的 `final_else`，防止重检块被误识别为 `elif` 分支。
2. `LoopRegion.get_if_branch_boundary_stop`：将 `else_blocks` 纳入 `boundary_stop`，防止嵌套 IfRegion 吸收 while-else 块。

### 验证
4 个簇 B 测试通过。

---

## 簇 C — while-True+break+continue break 归属（#9）

### 根因
`while True: if a: continue; if b: break; x = 1` 中，break 块（`if b` 真分支）被识别为独立 break_blocks 出口，break 作为独立语句发射，原 `if b` 的 body 退化为 `pass`，且 `x = 1` 被挤到 break 之后（死代码）。break 未作为 IfRegion 子节点嵌套入 if 体（违反「父引用子入口」）。

### 修复（`region_analyzer.py`）
1. NCPD（最近公共后必经节点）sink-merge 重置：当 merge 是非汇聚终态 sink（无正常后继且无外部汇聚前驱）时，重置 `merge = None`，避免非汇聚 break 块被当作 merge 点。
2. BREAK 角色预检：在 `_identify_conditional_regions` 中，若 then/else 后继是 BREAK 块且对侧不是 elif，将 merge 设为 fall-through 分支，使 break 归属 IfRegion 子节点。

### 验证
`test_r2_while_true_break_continue_mix.py` 通过。

---

## 簇 D — for-iter walrus 双重求值（#10）

### 根因
`for x in (n := g()):` 的 walrus `COPY; STORE_FAST n` 既被 `_loop_extract_for_iter_pre_stmts` 当作 pre_stmt 发射为 `n = g()`，又被 iter 表达式重建为 `(n := g())`，导致 `g()` 被调用两次（双重求值）。for_iter_setup 块被双重归属（违反「每块唯一归属」）。

### 修复（`region_ast_generator.py`）
在 `_loop_extract_for_iter_pre_stmts` 中识别 `COPY; STORE_*` walrus 模式：当 `COPY` 后跟 `STORE_*` 且后续非 store 序列时，将其保留在 iter 表达式中（不提取为 pre_stmt），避免双重求值。

### 验证
`test_r2_for_iter_walrus.py` 通过。

---

## 簇 E — for body del 重建（#11）

### 根因
`for i in r: del m[i]` 中循环体块（CPython 将 for-target `STORE_FAST i` + body `LOAD_GLOBAL m; LOAD_FAST i; DELETE_SUBSCR` + `JUMP_BACKWARD` 回边编入同一块）经 `_loop_handle_back_edge` 处理：过滤 for-target 后调用 `_generate_stmts_from_instrs([LOAD_GLOBAL m, LOAD_FAST i, DELETE_SUBSCR])`。但该方法仅处理 `STORE_SUBSCR`/`STORE_ATTR`/`STORE_*`/`POP_TOP`，**未处理 `DELETE_SUBSCR`/`DELETE_ATTR`**。`DELETE_SUBSCR` 落入缓冲，`_build_statement` → `expr_reconstructor.reconstruct` 不识别 `DELETE_SUBSCR` 返回 None/空，导致 `_generate_stmts_from_instrs` 返回空列表，被 `_build_effective_stmts` 的 `[Expr(Name('i'))]` 覆盖——`del m[i]` 退化为裸表达式 `i`，`DELETE_SUBSCR` 完全丢失。违反「每块唯一归属」。

### 修复（`region_ast_generator.py` :: `_generate_stmts_from_instrs`）
镜像 `STORE_SUBSCR`/`STORE_ATTR` 处理，新增 `DELETE_SUBSCR`/`DELETE_ATTR` 分支：将缓冲 `[LOAD_GLOBAL m, LOAD_FAST i, DELETE_SUBSCR]` 交由既有的 `_build_delete_stmt` 重建为 `Delete(targets=[Subscript(value=Name(m), slice=Name(i), ctx=Del)])`（即 `del m[i]`）。`_build_delete_stmt` 返回语句**列表**，故用 `_stmts.extend(...)` 而非 `append`，避免嵌套成「Unknown node: list」。

修复后 `_generate_stmts_from_instrs` 返回 `[del m[i]]`（1 语句），`_build_effective_stmts` 的 `[Expr(Name('i'))]`（1 语句）不满足 `len(eff) > len(gen)` 的覆盖条件，`del m[i]` 被保留。

### 关键代码位置
`_generate_stmts_from_instrs` 中 `STORE_ATTR` 分支之后、`STORE_FAST` 分支之前新增 `DELETE_SUBSCR`/`DELETE_ATTR` 分支（标记 `[R2-E fix]`）。

### 验证
`test_r2_for_body_del.py` 通过。反编译输出 `for i in r: del m[i]`，字节码等价。

---

## 簇 F — while body await 循环退化（#12）

### 根因
`async def f(): while a: await g()` 退化为 `if (a and await g()): return None`。两层缺陷叠加：

1. **await 轮询循环误抑制（`region_analyzer.py` :: `_is_await_polling_loop`）**：while 循环回边 B5→B3，自然循环体 = {B3(await setup), B4(await 轮询自循环), B5(回边重检)}。原 `_is_await_polling_loop` 仅检查「body 内含 SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT 三联」——而 while 体含 B4（轮询子循环）即满足，导致**外层 while 循环被误判为 await 轮询自循环而抑制**，while 完全消失（违反「嵌套即抽象节点」——await 应嵌套入 while body，而非吞并 while）。
2. **await setup 块重建缺失（`region_ast_generator.py`）**：即使 while LoopRegion 被正确识别，其 header（B3，await setup：`LOAD g; CALL; GET_AWAITABLE; LOAD_CONST None`）经 `_loop_handle_header` → `_loop_extract_self_loop_stmts` 处理，该方法不识别 await 模式，将末尾 `LOAD_CONST None`（SEND 参数）当作裸表达式，输出 `Expr(Constant(None))`，`await g()` 丢失。

### 修复

**修复 1（`region_analyzer.py` :: `_is_await_polling_loop`）**：追加 header 三联检查。CPython 将 `SEND+YIELD_VALUE+RESUME+JUMP_BACKWARD_NO_INTERRUPT` 编入**同一自循环块**（即轮询自循环的 header）。真正轮询自循环的 header 自身含三联；外层 while 的 header（await setup 块，含 `GET_AWAITABLE` 但无 `SEND/YIELD/JBNI`）不含三联 → 不抑制 → 正确物化为 LoopRegion。此检查是结构性的（基于 header 指令构成），不依赖操作码特例，符合算法 4 原则。

**修复 2（`region_ast_generator.py`）**：
- 提取 `_reconstruct_await_block_stmts(block)` 辅助方法，封装 await setup 块的重建逻辑（剥离 `GET_AWAITABLE`+`LOAD_CONST None`+`SEND` 协议指令，将前驱指令归约为 await 的 value 表达式并包裹 `Await`；依 fall-through 是否含 `STORE_*` 决定 `Expr(Await)` / `Assign(...=Await)`）。
- `_generate_block_statements` 中原内联 await 逻辑改为调用该 helper（行为不变，纯重构）。
- `_loop_extract_self_loop_stmts` 起始处：若 header 含 `GET_AWAITABLE`，委托 `_reconstruct_await_block_stmts` 重建，确保 while header（await setup）正确输出 `await g()`，而非 `None`。

### 验证
`test_r2_while_body_await.py` 通过。反编译输出 `while a: await g()`，字节码等价。await 轮询自循环（B4→B4）仍被正确抑制（其 header B4 含三联），仅外层 while 不再被误抑制。

---

## 回归验证

逐簇修复后全量回归。为排除 Round 02 全部修复（A–F）对基线的影响，使用 `git stash` 对比 pre-round-02 基线（`0afc835 LOOP round_01`）与当前（A–F 应用）状态：

| 指标 | 基线（pre-round-02） | 当前（A–F） | 结论 |
|------|---------------------|------------|------|
| `tests/exhaustive/loop/round_02/` | 12 failed | **12 passed** | ✅ 12/12 修复 |
| `tests/exhaustive/while_loop/` + `for_loop/` | 18 failed, 295 passed | **5 failed, 308 passed** | ✅ 5 ≤ 18，无新增失败（5 个均为基线既有 `l15whiletruebreak`/`wl30whilebreakintry`），13 个被 A–F 顺带修复 |
| `tests/exhaustive/loop/round_01/` | 5 failed, 9 passed, 2 skipped | **5 failed, 9 passed, 2 skipped** | ✅ 完全一致，5 个均为 R01 已知限制（#5 ternary-cond / #10 try-except-else-finally / #13 continue 嵌套 if / #14 四操作数链式比较 / #15 嵌套 for-else） |
| `tests/exhaustive/ternary/` | 22 failed, 483 passed, 42 skipped, 44 xfailed, 7 xpassed | **22 failed, 483 passed, 42 skipped, 44 xfailed, 7 xpassed** | ✅ 完全一致，无退化 |

**结论**：所有基线指标均满足约束（while/for ≤18 failed；ternary 无变化；R01 无退化），Round 02 修复 12/12 且零回归。

---

## 算法原则符合度

- **自底向上归约**：簇 F 中 await 轮询自循环（内层）先被抑制，外层 while LoopRegion 后物化，await 作为子节点嵌套入 while body。
- **每块唯一归属**：簇 E 中 `DELETE_SUBSCR` 块唯一归属 `Delete` 语句；簇 F 中 await setup 块唯一归属 `Await` 表达式（协议指令不归属用户语句）；簇 D 中 walrus 的 `COPY+STORE` 唯一归属 iter 表达式（不再重复提取为 pre_stmt）。
- **嵌套即抽象节点**：簇 F 中 await 表达式嵌套入 while body，而非并入 while 条件或吞并 while；簇 B/C 中重检块/else 块归条件/循环，不被跨区域吸收。
- **父引用子入口**：簇 C 中 break 作为 IfRegion 子节点嵌套入 if 体，由父 IfRegion 引用其入口。

无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无扁平化、无硬编码深度上限、无禁用前缀命名。
