# Round 59 OUTCOME — IQCommon/util/replace_utils.pyc 9/9

## 落地

四处结构性判据（均严格附加，不读名字/常量/绝对偏移/指令数），仅改 `core/cfg/region_ast_generator.py`（BOM+CRLF 保留），py_compile OK：

### R59 Fix1 — `_emit_post_extra_with_if_upgrade` 异常后继让位（~L38069+）
- **识别条件**：post-extra 升级路径中 `_exc`/`_claimable` 为真，或候选 continuation 落在当前 emit 块的 exception_successors 内。
- **归约方式**：`_r59_exc`/`_r59_claimable` 让位；后继扫描剔除 exception_successors，避免异常后继 996 覆写 `_continuation` 吞掉 then/merge。
- **AST 映射**：消掉伪 `if decrypted_url:`——success 路径回到 if 外兄弟序列。
- 凭据：probe 栈块 506 n=32 末 LOAD@682 succs=[996,684] exc=[996]；996 为异常边后继。

### R59 Fix2 — Ternary 分支 claim 前 `_r59_sr_types`（`_generate_region`）
- **识别条件**：三元子区域走 Ternary 发射路径且尚未标 generated，但其语句消费块属于另一 If/Merge 归约。
- **归约方式**：return `_ternary_ast` 前先 `_r59_sr_types` claim，防止 Ternary@292 标 generated 吞掉块 400。
- **AST 映射**：`IfRegion@400` 正常生成（then=[442,484,504,506,684] else=[] merge=686）。
- 凭据：R59 前 IfRegion@400 永不生成，块 400 被三元路径吸走。

### R59 Fix3 — `_if_generate_normal` ibc or 链负极性（~L17271）
- **识别条件**：`'IF_FALSE' in opname` 且 `argval ∈ then_blocks`（NONE_CHECK R75 翻转后的 or-chain 后续段）。
- **归约方式**：对 `_part` 施 `_negate_expr`（R13c `if not A or B:` 首段负极性，dis 实证）。
- **AST 映射**：`if not decrypted_url or '://' not in decrypted_url:` 形态正确。
- 凭据：R75 翻转后 or 链首段已带 not，后续段不再取反会双重否定/漏否定。

### R59 Fix4b — 三元 post_consumer 尾部 LOAD 联结 RETURN 后继（`_try_build_ternary_merge_consumer_expr` L40117-40173，`_r59u_*`）
- **识别条件**：`_rest_clean` 末指令为 LOAD_*；末段（最后 POP_TOP/STORE/RETURN 之后）全为 LOAD_*；`_rest_stmts[-1]` 为 Expr；merge_block 剔异常后唯一正常后继恰为单条 RETURN_VALUE/RETURN_CONST。
- **归约方式**：Expr→`Return(_explicit_return=True)` + 后继块标 generated。
- **AST 映射**：尾部 `LOAD_FAST url@682` 不再发成裸 Expr；`return url` 归入 then 分支。
- 凭据：块 506 语句经 `_if_generate_then_branch`→`_generate_ternary`→本函数，`block=None` 发裸 LOAD，后继块 684(RETURN_VALUE) 的 Return 曾丢失。Fix4（body 层 L42910+）对靶块 506 无效，必须在三元 consumer 层修。

诊断脚本：`D:\Temp\opencode\r59\`（probe_verify / probe_bs506 / probe_bsi_caller / probe_ternary_child / probe_regions506）。

## 靶面

| 尺 | 落地前 | 落地后 |
|---|---|---|
| 官方 `pyc_batch_verify single` | partial 8/9 | **ok 9/9 100%** |
| 严格 `_r10_strict_check` | 非全绿 | **9/9，文件级 1/1，真缺陷 0** |

目标形态（probe 实证）：
```
IfRegion@400: if not decrypted_url or '://' not in decrypted_url:
  then: log x3 + return url          # Fix4b 联结块684
  else: (success path, 在 if 外)
merge@686
```

## 门禁

- **G6** `batch --round 59`：402 verified / 0 failed；ok_pyc **377→378**、partial **25→24**。
- **G7** stats：total 5746 / matched **5671** / rate **98.69%**（达标 ≥98.69%）。
- **金丝雀** quotation strict **148/150** 缺陷集逐字不变（change_his_to_forward/get_trend）+ bytecode **143/143**；market_time **10/10**；function **71/71**。
- **无手改 *OK.py**：13 个 *OK.py 变化均为 `pyc_batch_verify` 工具生成。
- **pyc_index.json**：replace_utils.pyc `ok 9/9 last_tested_round=59 mismatch_count=0 status=ok`。

## 字节面（终值）

- `region_ast_generator.py`：sha `201ad020edb123441af4` / size 3052185 / BOM True / CRLF 49366 / 裸 LF 0 / py_compile OK。
- `region_analyzer.py`：本轮未改，sha `a67008a120f9dcf816b0` / size 1718595 / 无 BOM / CRLF 27546。

注：写入过程曾出现 1 处孤立 LF（`.post_consumer_extra_stmts = _rest_stmts\n\r\n`），已用 `data.replace(b'\n\r\n', b'\r\n\r\n')` 修复；写后必测 lfonly。

## 归档

`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round59/`
（OUTCOME.md）

起始 HEAD `a69089cd`（Round 58 记录）。
