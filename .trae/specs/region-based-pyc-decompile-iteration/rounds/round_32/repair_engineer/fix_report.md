# Round 32 修复报告：try-finally 内循环尾部布局（shape_c）+ frozenset 常量保留

日期：2026-08-30　修复人：修复工程师　基线：ok=307 / partial=95，funcs=5427/5746（Round 31）

## 1. 根因（已亲自实测验证）

### 1.1 ptradeAccount order/trade_response_order_update 97/126 指令截断

- 现象：`order_response_order_update` 原 97 指令反编译后仅 30 指令，循环体大部分
  丢失；`trade_response_order_update` 原 126 指令反编译后仅 33 指令。probe 确认
  区域结构为 `TryExceptRegion(4) try_blocks 含循环` + `finally=[550,614]` +
  `Region(620)`（`LOAD_CONST None; RETURN_VALUE`）。
- Probe 分步追踪（repair_engineer/probe_fle2.py 等）发现双重根因：
  (a) **异常后继被误当 break 目标**：循环体内块（230/360）的异常边（try-finally
  handler 入口 550）不是 break 目标。旧逻辑把异常后继当 break 目标，使
  try-finally 内循环错误进入 break_targets 分支（post_else BFS），绕过
  no-break 分支的 NOP 判别器，导致 phantom for-else 仍被吞并。
  (b) **NOP 判别器需三态**：bool 返回无法区分「有 try 但无 NOP」（确定非
  for-else）与「无 try」（判别器不适用，需保持原启发式）。改为
  True/False/None 三态。
- Pattern A fix 补充：`Region(620)` 的展开块末指令是 `JUMP_FORWARD`（handler
  跳过跳转，显式 `return None` 的唯一合法形态），此前被 `all_blocks` 吸收后
  静默丢失；需释放为独立 BASIC 区域发射。

### 1.2 frozenset 常量被误转 tuple

- 现象：`trade_response_order_update` 中 `if status in {5, 6}:`（原始
  `LOAD_CONST frozenset({5,6}); CONTAINS_OP`）反编译输出 `if status in (5, 6):`，
  重编译产生 BUILD_SET 序列，co_code/co_consts 不一致。
- 链路追踪（probe_hook_ccf/probe_compare_chain/probe_pyc_code）：AST dict 与
  converter 均正确保留 frozenset，差异在解析层
  `core/pyc_objects.py::PycCode.to_python_code` 的 `_resolve_ref`——所有
  `PycSequence` 无条件转为 tuple，`TYPE_FROZENSET`/`TYPE_SET` 一并被转。
- 实证（probe_compile_set.py，CPython 3.11）：`status in {5, 6}` 编译为
  `LOAD_CONST frozenset({5,6}); CONTAINS_OP`，与原始字节码完全一致，是正确
  渲染目标。

### 1.3 t_nested 显式 Continue 改变 try 异常表边界

- `try-except` 作为循环体最后一条语句时，except 处理器以
  `POP_EXCEPT+JUMP_BACKWARD→header` 收尾，该回边是循环的隐式迭代；按
  CONTINUE 角色补发显式 Continue 会改变 try 异常表边界（orig 40 vs 41 指令）。

## 2. 改动

- `core/cfg/region_analyzer.py`（+227 行，7 处）
  - TryExceptRegion 配对 vs 嵌套判别（`try_offset_start` 相等性）：真嵌套
    （内层 try 在外层 try body 中）必须保持子区域，绝不吸收；
  - `_clamp_loop_else_to_enclosing_try`：else_blocks 不越过包围 try 的 offset
    边界，防止 LoopRegion range 反超 TryExceptRegion 导致层级颠倒；
  - `_loop_else_nop_marker` 三态 NOP 判别器（try/finally 上下文 for-else 的
    编译器特征，nop_marker2.py w1-w8 实证）；
  - `_find_loop_else` break 扫描排除 `block.exception_successors`；
  - `_find_loop_else` 无 break 分支接入三态 NOP 判别器；
  - Pattern A fix 显式 return 判别器（展开块末指令 `JUMP_FORWARD` → 释放
    Region(620) 为独立 BASIC 区域）；
  - `add_child` 守卫同步配对/嵌套判别（2 处，真嵌套必须建立子关系）。
- `core/cfg/region_ast_generator.py`（+134 行，3 个新方法 + 2 处应用）
  - `_block_is_pure_back_edge_to_header`：纯 JUMP_BACKWARD→header 回边块判定；
  - `_if_false_path_is_loop_iteration`：if 假出口直通纯回边块 → if 是循环体
    最后一条语句，then 末尾独立回边块是隐式迭代，不得补发显式 Continue；
  - `_handler_backedge_is_natural_loop_iteration`：except 处理器末尾回边块
    之后无待执行普通语句 → 隐式迭代，不补发 Continue。
- `core/pyc_objects.py`（+8 行）
  - `to_python_code._resolve_ref`：`PycSequence` 按 `_type` 分派——
    `TYPE_FROZENSET` → `frozenset(...)`、`TYPE_SET` → `set(...)`、其余 →
    `tuple(...)`（修复前无条件转 tuple）。

## 3. 验证结果（全部实测）

| 步骤 | 命令/方式 | 结果 |
|---|---|---|
| a. 目标函数 | `verify_fix.py`（F_return_after_finally + ptradeAccount 两函数） | F_return_after_finally 1/1；order_response_order_update 匹配；trade_response_order_update 匹配 |
| a2. frozenset 复验 | `verify_fix.py`（修复 `_resolve_ref` 后） | 3 目标函数全部 matched |
| b. ptradeAccount 全函数 | `verify_ptrade_full.py`（co_code/consts/names/varnames 全等） | 134/136（HEAD 基线 132/136，净提升 +2，无回归） |
| b2. 无回归对照 | git stash 回退至 HEAD 重测 | 4 mismatch（含本轮 2 目标）；修复后 2 mismatch（PtradeAccount NOP、stock_order if-or-elif 翻转，均为历史遗留，非本轮引入） |
| c. 定向回归 | `verify_regression.py` | t_nested 1/1、t_paired 1/1、F_return_after_finally 1/1、ptradeAccount 目标 2/2 |
| d. 全量回归 | `pyc_batch_verify.py batch`，PYTHONHASHSEED=0，402 pyc，3m07s | ok=309（+2）/ partial=93 / failed=0；函数级 4857/5149（94.33%，Round 31 基线 5427/5746）；倒退 0、改进 2（op_station、ptradeAccount 135/137→137/137，见 scan_after_fix.json） |
| d1. 补丁合规 | `scripts/check_patch_patterns.py` | PASS（region_analyzer.py / region_ast_generator.py 均 OK） |
| d2. opcode 计数 | `scripts/check_hardcoded_opcodes.py` | region_analyzer=694（Round 31: 690，+4）、region_ast_generator=1363（Round 31: 1362，+1）；新增均为本轮判定逻辑所需（NOP 判别器、纯回边/异常指令判定），无危险模式 |

## 4. 已知遗留（Round 33 候选）

- `ptradeAccount::stock_order_response_transform`：`if A or B: X elif C: Y`
  被错误解构为 `if not A: [if B: X elif C: Y]`，A true 时 X 丢失（语义错误，
  非纯字节码差异）。
- `ptradeAccount::PtradeAccount` 类体：函数定义前行号锚点 NOP 缺失，co_code
  差 8 字节（471 vs 467）。

## 5. 附件

- `probe_frozenset.py` / `probe_astdict_fs.py` / `probe_conv_full.py` /
  `probe_hook_gen.py` / `probe_hook_conv.py` / `probe_hook_conv2.py` /
  `probe_hook_v2.py` / `probe_hook_ccf.py` / `probe_compare_chain.py` /
  `probe_pyc_code.py` / `probe_module_dict.py` / `probe_compile_set.py`：
  frozenset 转换链路逐步定位；
- `probe_diff2*.py` / `probe_diff3.py`：遗留 mismatch 字节码对比；
- `verify_fix.py` / `verify_ptrade_full.py` / `verify_regression.py`：验证脚本；
- `scan_after_fix.json`：全量回归逐文件明细。
