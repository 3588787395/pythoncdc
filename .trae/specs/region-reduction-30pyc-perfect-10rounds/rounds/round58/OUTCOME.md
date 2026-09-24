# Round 58 OUTCOME — plugin_system_event_source/default_event_source.pyc 14/14

## 落地

三处结构性判据（均严格附加，不读名字/常量/绝对偏移/指令数），文件 `core/cfg/region_analyzer.py`（无 BOM + CRLF）与 `core/cfg/region_ast_generator.py`（BOM + CRLF 保留），py_compile OK：

### R58-B Fix1 — `_find_loop_else` 纯跳转 for_iter_exit 直返（region_analyzer ~5292）
- **识别条件**：for_iter_exit 为单条 JUMP_FORWARD/JUMP_ABSOLUTE 纯跳转且 post_else ≠ for_iter_exit。
- **归约方式**：直接 `return [for_iter_exit], natural_exit`，不做 BFS、不过纯跳转过滤——else 块即该纯跳转块本身。
- **AST 映射**：`LoopRegion.else_blocks = [for_iter_exit]`；实证 for@2708 else=[3208]（JUMP_FORWARD→3214）。
- 凭据：原 BFS 会把 break 目标 3214 吞进 else 可达集导致 else 与 break 目标混淆。

### R58-B Fix2 — `_cleanup_try_else_in_loop_body` metadata 豁免（region_analyzer ~4716）
- **识别条件**：cleanup 在 L1789 执行、`_annotate_all_roles` 在 L1791——cleanup 时 block_roles 全为 NORMAL，角色判据不可用；改用 `lr.metadata.get('for_iter_exit')` 比对。
- **归约方式**：spurious 判据加 `and eb is not _r58_fie`，保留 for_iter_exit 块。
- **AST 映射**：cleanup 后 else=[3208] 不被误删。
- 凭据：第一版按 BlockRole.BREAK/PURE_BREAK 过滤失败（cleanup 时角色未标注）。

### R58-B Fix3 — break 核验 R30-C1 前向跳转前驱豁免（region_analyzer ~4329）
- **识别条件**：break 目标末指令为 BACKWARD_JUMP 且落点≠header 时，若 body 内存在经 JUMP_FORWARD/JUMP_ABSOLUTE 直入该目标的前驱则豁免。
- **归约方式**：`has_break=True`、`break_blocks` 保留；实证 for@2708 break=[3210]、while@2476 break=[3214]。
- **AST 映射**：`LoopRegion.has_break/break_blocks` 正确标注。
- 凭据：原核验误拒 break 目标 3210（EXTENDED_ARG+JUMP_BACKWARD→2476，落点=while header≠for header）。

### R58-B Fix4 — while 非平凡 break 目标顺序发射（region_ast_generator `_r58_collect_break_target_stmts` + path A/B/C 调用）
- **识别条件**：`region.has_break=True` 且 break 目标块含非平凡代码（非 PURE_JUMP/条件跳转/POP_TOP/EXTENDED_ARG），该块是循环后顺序代码入口。
- **归约方式**：entry 区域为 If/Loop/Try 则递归生成；entry 区域为 region 自身或 busy 时直接生成块语句；标记 generated 防重复。`while True` 早退路径（path A/B/C）在 return 前调用并 extend 到 output。
- **AST 映射**：`[While, Assign(dt=date.replace), Expr(yield AFTER_TRADING_END)]` 兄弟序列。
- 凭据：while@2476 break 目标 3214 = `dt/yield` 段；原实现 while 路径缺非平凡 break 目标发射逻辑，3214 被吸入 region_blocks 却从不发射。

### R58-B Fix5 — for-else 纯跳转 else 归约为 Break（region_ast_generator ~4775）
- **识别条件**：for 循环有 else_blocks，但 `_if_generate_branch_stmts` 产出为空（else 块仅含 PURE_JUMP/NOISE），且所有 else 块直接后继均落在某个祖先 LoopRegion 的 break_blocks 中。
- **归约方式**：归约为 `[{'type': 'Break'}]`，标记 else 块 generated。
- **AST 映射**：`For.orelse = [Break]`；实证 for@2708 orelse=[Break]（else@3208 JUMP_FORWARD→3214 ∈ while@2476.break_blocks）。
- 凭据：原 `_if_generate_branch_stmts([3208])` 返回 0（纯跳转无用户语句），orelse 缺失导致 FOR_ITER 耗尽路径发成 JUMP_BACKWARD 2476（continue while）而非 JUMP_FORWARD 3214（exit while）。

## 靶面

| 尺 | 落地前 | 落地后 |
|---|---|---|
| 官方 `pyc_batch_verify single` | partial 13/14，true_diffs=30，decomp=492/510 | **ok 14/14 100%** |
| 严格 `_r10_strict_check` | 13/14 seq_len orig=512 decomp=511 | **14/14** |
| lockstep diff | total_midx_divergent=29，len_diff=1 | **0，len_diff=0** |

目标形态（trace_struct 实证）：
```
LoopRegion@2708: For orelse=[Break]           # else: break (while)
LoopRegion@2476: [While(body=[Assign,If,Assign,For]), Assign(dt), Expr(yield)]
While.body[3] = For with orelse=[Break]
```

关键字节码流（orig=decomp）：
```
3204 JUMP_FORWARD 3210   # if universe_changed 内 break → while 回边
3206 JUMP_BACKWARD 2708  # for 正常继续
3208 JUMP_FORWARD 3214   # for-else → while break 目标 (dt/yield)
3210 JUMP_BACKWARD 2476  # break 目标 → while 继续
3214 LOAD_FAST date ...  # while 后 dt/yield
```

## 门禁

- **G6** `batch --round 58`：402 verified / 0 failed；ok_pyc **376→377**、partial **26→25**、failed 0。
- **G7** stats：total 5746 / matched **5671** / rate **98.69%**（与 R57 持平——本轮收益在靶本身 partial→ok，matched_functions 不变因 events 原已计入 13/14 中的 13）。
- **金丝雀** quotation strict 148/150 缺陷集合逐字不变（change_his_to_forward/get_trend）；market_time 10/10；function 71/71。
- **无手改 *OK.py**：default_event_sourceOK.py 等为 `pyc_batch_verify` 工具生成。
- **pyc_index.json**：default_event_source.pyc `ok 14/14 last_tested_round=58 mismatch_count=0 status=ok`。

## 字节面

- `region_analyzer.py`：sha `a67008a120f9dcf816b0` / size 1718595 / 无 BOM / CRLF 27546 / 裸 LF 0。
- `region_ast_generator.py`：sha `53a6158f044919a87811` / size 3038927 / BOM True / CRLF 49161 / 裸 LF 0。

## 归档

`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round58/`
（OUTCOME.md + 诊断脚本说明）

起始 HEAD `d39b23a0`（Round 57 记录）。
