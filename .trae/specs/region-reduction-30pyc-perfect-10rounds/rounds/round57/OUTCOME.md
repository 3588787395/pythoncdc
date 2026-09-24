# Round 57 OUTCOME — plugin_system_trade/function.pyc 71/71

## 落地

三处结构性判据（均严格附加，不读名字/常量/绝对偏移/指令数），文件 `core/cfg/region_ast_generator.py`（BOM + CRLF 保留，py_compile OK）：

### R57-B Fix1 — `_process_if_blocks` BREAK 分支（~21075）
- **识别条件**：BREAK/PURE_BREAK 角色块带有效语句，且其全部非异常正常后继恰为本 `IfRegion.merge_block`，且该 merge 角色亦为 BREAK/PURE_BREAK（真臂 fall-through 与条件假边双前驱共享 break 中转桩）。
- **归约方式**：仅发射块内有效语句、不追加 Break，且不认领 merge——交父层/后置路径把 merge 作为 if 后兄弟 Break 发射一次。
- **AST 映射**：`stmts += 有效语句`；merge 的 Break 由 post-if 或兄弟扫描发射。
- 凭据：`@1040`（error 调用）后继仅 `merge@1298`，原实现臂内多发 Break + TCBB 吞 merge 导致 shared trampoline 丢失。

### R57-B Fix2 — TCBB break+normal（~22668）
- **识别条件**：break+normal 四组合映射中，break 后继恰为**包含本条件块**的某 `IfRegion.merge_block`（两路在 if 后重逢，非独占 else 出口）。
- **归约方式**：该侧不发 Break、orelse/then 置空，且不把 break 目标记为 generated——交父层把 merge 作 if 后兄弟语句发射。
- **AST 映射**：`If(test, body=正常臂, orelse=[])`；merge 由 post-if/兄弟发射。
- 凭据：`@1238` POP_JUMP_IF_FALSE→`merge@1298` 被发成 `else: break`，真臂路径语义反转。

### R57-B Fix3 — `_mb_in_nested_structural`（`_if_generate_normal` ~17840 + elif 镜像 ~12545）
- **识别条件**：Try/With/Match 沿 `region.parent` 链可达（本 IfRegion 嵌在其 blocks 内 = **祖先**，而非嵌套在本 if 臂内的子结构）。
- **归约方式**：祖先压不住 post-if/elif 后置发射（merge 归本区域作 if 后兄弟语句），仅后代结构可压制。
- **AST 映射**：post-if 照常发射 merge；后代结构内的 merge 仍不发。
- 凭据：外层 `TryExceptRegion@4` 包含一切导致 merge@1298 被误判 nested、post-if 被压制。

## 靶面

| 尺 | 落地前 | 落地后 |
|---|---|---|
| 官方 `pyc_batch_verify single` | partial 70/71 | **ok 71/71 100%** |
| 严格 `_r10_strict_check` | 70/71 seq_len +1~+2 | **71/71** |

目标形态（trace_else958 实证）：
```
if@980 then=['Expr'] orelse=['If','If']
if@958 then=['Assign','If','Break']  # Break@1298 为 if 后兄弟
TCBB@1238 -> If body=['Assign'] orelse=None  # 不再 else:break
```

## 门禁

- **G6** `batch --round 57`：402 verified / 0 failed；ok_pyc **375→376**、partial **27→26**、failed 0。
- **G7** stats：total 5746 / matched **5669→5671** / rate **98.66%→98.69%**。
- **金丝雀** quotation strict 148/150 缺陷集合逐字不变；market_time 10/10。
- **复现电池** `run_repros.py`：19 例 **MATCH=17 MISMATCH=2**（r57_11/r57_19 仅模块级 docstring 伪造 +2，与本修复无关）；3 负对照全 MATCH。
- **无手改 *OK.py**：7 支 OK 变化均为 `pyc_batch_verify` 工具生成（finance/trade_info_utils/realtime_event_source/matcher/function/trade_live_broker/quote）。
- **pyc_index.json**：function.pyc `ok 71/71 last_tested_round=57 mismatch_count=0`；26 支 partial 轮次戳 56→57。

## 归档

`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round57/test_engineer/`
（ANALYSIS.md + 19 支 minimal_repros + run_repros.py + repro_results.jsonl）

起始 HEAD `24498437`（Round 56 记录）。
