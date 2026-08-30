# Round 31 修复报告：make_trade elif 链 final else 嵌套 if/else 语句丢失

日期：2026-08-30　修复人：修复工程师　基线：ok=306 / partial=96，funcs=5425/5746

## 1. 根因（已亲自实测验证）

- 现象：`future_position.pyc::make_trade`（71/72）final else 内嵌套 if/else 的
  orelse 两条赋值（`self._long_clean_time = current_date`、
  `self._buy_avg_open_price = 0.0`）在产物中消失，真分支 JUMP_FORWARD 被内联。
- Probe 实测（repair_engineer/probe_flags.py，PYTHONHASHSEED=0）：渲染层
  `core/cfg/code_generator.py::_generate_elif_or_else` 收到
  `orelse.nodes = [If(test=ASTCompare, _is_elif=False, _is_nested_if=False,
  orelse=[2 条赋值]), merge 语句×5]`。内层 If 两个既有逃逸分支
  （`_is_nested_if` 标记、`_test_is_simple_variable`）均不命中，被误判为
  elif 渲染；随后 `len(orelse.nodes) > 1` 分支把 merge 兄弟语句顶替成 else
  体，内层 If 自身的 orelse 被静默丢弃。
- 上游区域分析输出正确（`elif_final_else=[1272,1300,1414,1442]`、
  `_process_if_blocks` 返回的 AST 完好，merge 折入 final else 属实），语句
  丢失纯发生在渲染层——与测试工程师判断一致。`_generate_if`（1377-1400 行）
  对"链臂+尾随兄弟"已有正确的抑制展平逻辑，但该抑制未覆盖 1416 行递归进
  `_generate_elif_or_else` 后的同类场景。

## 2. 改动

- 文件：`core/cfg/code_generator.py`（唯一源码改动，+26 行，
  `_generate_elif_or_else` 内，约 1753-1781 行）。
- 逻辑：在 elif 渲染判定前新增结构检查——当
  `orelse.nodes = [If, 兄弟语句...]` 且 If 未标记 `_is_elif`、其自身 orelse
  有实际内容（过滤 return None 后非空）时，该 If 是 else 中的嵌套 if/else
  （elif 链在此结束），整个块按 else 体渲染：嵌套 if/else 在前，兄弟语句
  （链 merge 折入 final else 的内容）保序跟在其后，不再丢弃任何节点。
  即"elif 链最深层的 orelse 包含兄弟语句"，符合区域归约算法语义，无任何
  opcode 硬编码或特判。
- 生成行为：`future_positionOK.py` 由验证工具重新生成（允许行为），diff
  即为恢复的两条赋值与嵌套结构。

## 3. 验证结果（全部实测）

| 步骤 | 命令/方式 | 结果 |
|---|---|---|
| a. 最小复现 | `pyc_batch_verify.decompile_single` + `bytecode_diff`（repro_r31_make_trade_mirror.pyc） | 7/7 全匹配（修复前 6/7，make DIFF），make 函数 BYTE-IDENTICAL |
| a2. 对照 v1 | repro_r31_elif_else_merge.pyc | 5/5 不回归 |
| b. 目标文件 | round_30 `list_mismatch.py` future_position.pyc | 72/72 全匹配 rate=1.0000（71/72 → 72/72） |
| c. 全量回归 | round_06 `full_scan.py`，PYTHONHASHSEED=0，402 pyc，737.6s | ok=307 / partial=95 / failed=0，funcs=5427/5746 |
| c2. 逐文件对比 | 与 round_30 基线 scan_r30c.json 对比 | 倒退 0；改进 2：future_position(partial 71/72→ok 72/72)、strategy_info_utils(23/28→24/28) |
| d1. 补丁合规 | `scripts/check_patch_patterns.py` | PASS |
| d2. opcode 计数 | `scripts/check_hardcoded_opcodes.py` | region_analyzer=690、region_ast_generator=1362 ≤ 1364（本次改动文件 code_generator.py 不在扫描范围，计数与修复前一致） |

## 4. 附件

- `probe_flags.py`：根因验证 probe（dump `_generate_elif_or_else` 入口节点属性）
- `scan_after_fix.json`：全量回归逐文件明细
