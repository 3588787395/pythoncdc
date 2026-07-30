# R08 测试工程师报告 — graph.pyc Pattern T3（嵌套 try-except in loop）

## 1. 目标 pyc 与状态

| 字段 | 值 |
|---|---|
| 轮次 | R08 (rcm-r08) |
| 目标 pyc | `IQCommon/graph.pyc` |
| 取 pyc 依据 | R07 残留 Pattern T3（graph.pyc `failed`，`failed` 优先级高于 `partial`/`pending`） |
| function_count | 40 |
| R07 状态 | **failed**（load_compiled_failed: graphOK.py 含 SyntaxError: expected 'except' or 'finally' block，0/0 函数可比对） |
| R08 状态（修复前） | **failed**（同 R07，graphOK.py L114 `def append_graph` 前缺 except，SyntaxError） |
| R08 状态（修复后） | **partial**（87.10%，27/31 函数一致，4 mismatches；graphOK.py 编译通过） |

## 2. 反编译 + 字节码 diff 结果（修复前）

```
python scripts/pyc_batch_verify.py single ".../graph.pyc"
  decompile_status:   failed
  total_functions:   0
  matched_functions: 0
  match_rate:        0.00%
  error: load_compiled_failed: TypeError: expected str, bytes or os.PathLike object, not NoneType
```

graphOK.py 编译错误（py_compile）：
```
File ".../graphOK.py", line 114
    def append_graph(self, edges):
SyntaxError: expected 'except' or 'finally' block
```

定位到 `create_full_graph` 函数（graphOK.py L80-113）：
- 外层 `try:` 关键字**完全缺失**
- 外层 `except BaseException:` 被误生成为 `if BaseException:`（L100）
- 循环后代码（`add_nodes_from`/`add_edges_from`/`return`）被错误地放进 for-loop 体内，并被一个幻影 `try:` 包裹（L106-113）
- 内层 `try/except KeyError`（L93-99）正确

## 3. 原始字节码结构（create_full_graph，关键 offset）

```
14   NOP                          # OUTER try 起点（try_offset_start=14）
42   FOR_ITER 532                 # for-loop header
316  NOP                          # INNER try 起点
318  LOAD_FAST self / _relation   # INNER try body
406  JUMP_BACKWARD 42             # loop back-edge（INNER else_blocks）
408  PUSH_EXC_INFO                # INNER handler_entry（KeyError）
426  ...                          # INNER handler body
524  RERAISE 0                    # INNER cleanup
532  add_nodes_from / add_edges_from  # post-loop 代码（OUTER try body 续）
636  RETURN_VALUE                 # 正常返回
640  PUSH_EXC_INFO                # OUTER handler_entry（BaseException）
642  LOAD_GLOBAL BaseException / CHECK_EXC_MATCH  # OUTER handler entry 续
658  ...                          # OUTER handler body
762  RERAISE / cleanup            # OUTER cleanup
```

OUTER try-offset-range: [14, 638]；OUTER handler_entry=640；INNER try-offset-range: [316, 406]；INNER handler_entry=408。

## 4. Pattern T3 诊断

### 4a. 区域识别结果（diag_pattern_t3.py）

| 区域 | entry | parent | try_blocks | handler_entry_blocks |
|---|---|---|---|---|
| LoopRegion | 42 | None (top) | — | — |
| TryExceptRegion (OUTER) | 14 | **LoopRegion（错误）** | [14,42,44,94,206,282,316,532,638] | [640] |
| TryExceptRegion (INNER) | 318 | TryExceptRegion(OUTER)（正确） | [318] | [408] |
| IfRegion | 44 | TryExceptRegion(OUTER) | — | — |

- `block_to_region[640] = OUTER`（权威归属正确）
- OUTER.entry (14) 在 LoopRegion.blocks 内（因为 14 是 for_iter_setup 块）→ parent 误判为 LoopRegion（独立残留，非本轮 scope）

### 4b. 生成阶段 trace（diag_trace_t3.py）

生成顺序：`_generate_loop(42)` → 递归 `_generate_try(INNER 318)` → 递归 `_generate_try(OUTER 14)`。

**INNER _generate_try 关键 trace**：
- `generated_blocks BEFORE`: [0,42,44,94,206,282,316]
- `generated_blocks AFTER`: [...,318,406,408,426,520,524,526,**640,658,758,762,764**]
- 结果: `[Try(handlers=1), If(test=Name(BaseException), body=[Assign×3,Expr,Return])]`

**OUTER _generate_try 关键 trace**：
- `generated_blocks BEFORE` 已含 640,658,758,762,764
- 结果: `Try(handlers=0, body_len=7)` ← **0 handlers！**

### 4c. 根因（1 段）

`_generate_try` 的 post-try 块检测有两条收集分支：else_blocks 分支（L15830-15854）与 try_blocks 分支（L15873-15896）。两条分支均未查询 `block_to_region` 权威归属映射。INNER 的 `else_blocks=[block@406]`（loop back-edge 块 JUMP_BACKWARD→42），其 CFG 后继经异常边指向 OUTER 的 `handler_entry` block 640。else_blocks 分支把 640 收集为 INNER 的 post-try 块并标记 `generated`，进而 640 的后继（658/758/762/764，即 OUTER 的 handler body + cleanup）也被收集并标记。随后 OUTER 的 `_generate_try` handler 循环 `if handler_entry in self.generated_blocks: continue` 跳过 640 → 0 handlers → `try:` 无 `except:` → SyntaxError。这与 R07 Pattern T 同源（生成层块标记循环缺归属守卫），但位置不同（`_generate_try` post-try 检测 vs `_generate_with`/`_process_if_blocks` 标记循环），且触发结构不同（嵌套 try in loop，无 with）。

## 5. 最小复现实例（14 个）

| # | 文件 | 模式 | 修复前 | 修复后 |
|---|---|---|---|---|
| 01 | repro_01_nested_try_in_for.py | for + 嵌套 try（最小） | NO-DEFECT | NO-DEFECT |
| 02 | repro_02_nested_try_in_while.py | while + 嵌套 try | DEFECT-REPRO (32 td) | DEFECT-REPRO (35 td) |
| 03 | repro_03_nested_try_except_finally_in_for.py | for + try/except/finally | DEFECT-REPRO (49 td) | DEFECT-REPRO (49 td) |
| 04 | repro_04_nested_try_in_for_continue.py | for + continue | NO-DEFECT | NO-DEFECT |
| 05 | repro_05_nested_try_in_for_break.py | for + break | DEFECT-REPRO (33 td) | DEFECT-REPRO (33 td) |
| 06 | repro_06_nested_try_in_for_return_in_except.py | for + return in except | DEFECT-REPRO (21 td) | DEFECT-REPRO (21 td) |
| 07 | repro_07_nested_try_in_for_return_in_try.py | for + return in try | DEFECT-REPRO (6 td) | DEFECT-REPRO (6 td) |
| 08 | repro_08_nested_try_in_for_assign_in_except.py | for + assign in except | NO-DEFECT | NO-DEFECT |
| 09 | repro_09_deeply_nested_try_in_try_in_for.py | 三层嵌套 | NO-DEFECT | NO-DEFECT |
| 10 | repro_10_nested_try_in_for_with_else.py | for + try-else | NO-DEFECT | NO-DEFECT |
| 11 | repro_11_mirror_create_full_graph.py | 镜像 create_full_graph | **ERROR (SyntaxError)** | **DEFECT-REPRO (76 td，编译通过)** |
| 12 | repro_12_ctrl_try_no_loop.py | CTRL 无 loop | NO-DEFECT | NO-DEFECT |
| 13 | repro_13_ctrl_loop_try_no_outer.py | CTRL 无外层 try | NO-DEFECT | NO-DEFECT |
| 14 | repro_14_nested_try_in_for_postloop_assign.py | for + post-loop assign | NO-DEFECT | NO-DEFECT |

- 修复前：6 DEFECT（5 DEFECT-REPRO + 1 ERROR），8 NO-DEFECT
- 修复后：6 DEFECT-REPRO，8 NO-DEFECT
- **repro_11（Pattern T3 精确镜像）从 ERROR（SyntaxError）→ DEFECT-REPRO（编译通过，76 residual diffs 为独立模式）**：T3 语法错误已修复
- 其余 DEFECT-REPRO（02/03/05/06/07）为不同缺陷模式（while/finally/break/return 变体），非 T3 scope
- 全部 8 个 NO-DEFECT 修复前后不变（零回归）

## 6. 与上一轮对比

| 指标 | R07 | R08（修复后） |
|---|---|---|
| graph.pyc 状态 | failed (0/0, SyntaxError) | **partial (27/31, 87.10%)** |
| graphOK.py 编译 | 失败（SyntaxError） | **通过** |
| 累计成功率（tested pycs） | 58.99% | **70.90%** |
| failed pyc 计数 | 3（backtest/main/graph） | **2**（backtest/main；graph 解锁） |

## 7. 残留问题

### 本轮残留（graph.pyc 4 个 mismatch 函数）

- `create_full_graph`（75 true_diffs）：OUTER try parent 误判为 LoopRegion（block 14 = for_iter_setup 在 LoopRegion.blocks 内）→ OUTER try 生成位置/结构偏差。独立残留。
- `_get_influence_task`（181 td）、`_process_task_queue`（359 td）、`is_cycle`（20 td）：不同的 try-except / 作用域模式，非 T3。

### 跨轮残留（不变）

Pattern A2 / B / C / E / F / M2 / T2 / repro_05 trailing-return — 见 R07 fix_report §8。
