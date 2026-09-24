# Round 60 OUTCOME — IQCommon/manager/instance.pyc 32/32

## 落地

两处结构性判据（均严格附加，不读名字/常量/绝对偏移/指令数），仅改 `core/cfg/region_ast_generator.py`（BOM+CRLF 保留），py_compile OK：

### R60 Fix1 — then 臂纯 RETURN 后继让位父区域（~L22171）
- **识别条件**：`branch=='then'` ∧ then 末块以 JUMP_FORWARD/JUMP_ABSOLUTE 直达后继 ∧ 后继单条 RETURN_VALUE ∧ 后继 ∉ 本 IfRegion.blocks ∧ 该 RETURN 块被外层 TryExcept/Loop/With/Match 区域 blocks 持有（扫 `region_analyzer.regions` 找 `_r60_ext_owner`）。
- **归约方式**：`continue` 不拉入 then 体——它是 if 之后由父 try 体发射的共享 return（原则 4：父区域持有该块）；else 落空拉入保留（else 内 return）。
- **AST 映射**：`If(test, then_body, orelse)` 之后由父 try 体发 `return None`。
- 凭据：IfRegion@66 merge=None then=[110] else=[172]；blk@110 末 JUMP_FORWARD→196（纯 RETURN、∈ Try@66/@4 blocks、∉ IfRegion.blocks）；无 Fix1 时 then 内联 return 致异常表与官方不一致（37 true_diffs）。

### R60 Fix2 — BoolOp `_has_if_like_then` 剔异常后继（~L33273）
- **识别条件**：链末块 `_lc.successors` 含 exception_successors（如 PUSH_EXC_INFO 处理器 88）。
- **归约方式**：`_r60_exc` 剔除异常边后再判 `_s is not _jt and _s not in region.blocks`——try 保护内 BoolOp 不再因异常后继误判 if-like。
- **AST 映射**：`_merge_is_return_only ∧ not _has_if_like_then` → `Return(boolop_expr)`（`return a or b`），不再降级为 `if not (...): pass`。
- 凭据：datetime BoolOpRegion entry=4 merge=86；`_lc` 后继 [86, 88] exc=[88]；88=PUSH_EXC_INFO。

诊断脚本：`D:\Temp\opencode\r60\`（trace_fixes / diag_candidates / diag_init / dump_cfg_regions / dump_full / dump_regions / trace_gen / dump_init_dt）。

## 靶面

| 尺 | 落地前 | 落地后 |
|---|---|---|
| 官方 `pyc_batch_verify single` | partial 31/32（`_init_config` 37 true_diffs） | **ok 32/32 100%** |
| 严格 `_r10_strict_check` | 31/33（`_init_config` 87/86、`datetime` 26/32） | **33/33，文件级 1/1，真缺陷 0** |

目标形态：
```
_init_config: if cond: FlyDataSource(...) / else: FlyDataSource(); return None / return None
datetime: return self._instance_engine.datetime or datetime.datetime.now()
```

## 门禁（真基线对照）

- **基线建立**：HEAD 生成器（R59 sha 201ad020edb123441af4）跑 `batch --all` → **ok 373 / partial 29 / matched 5665 / 98.59%**（HEAD 提交索引中 5 支陈旧 ok 为 R56 后未复验的潜伏 partial，与 R60 无关）。
- **G6** R60 `batch --all --round 60`：402 verified / 0 failed；ok **373→374**、partial **29→28**、matched **5665→5666**、rate **98.59%→98.61%**；逐文件对照 **REGRESSIONS=0、IMPROVED=1（仅 instance）**。
- **G7** stats：total 5746 / matched **5666** / **98.61%**。
- **金丝雀** quotation strict **148/150** 缺陷集逐字不变（change_his_to_forward/get_trend）+ bytecode **143/143**；market_time **10/10**；function **71/71**。
- **无手改 *OK.py**：*OK.py 变化均为 `pyc_batch_verify` 工具生成（含 `--all` 复验揭示的潜伏内容差，双基线一致）。
- **pyc_index.json**：instance.pyc `ok 32/32 last_tested_round=60 mismatch_count=0 status=ok`。

## 字节面（终值）

- `region_ast_generator.py`：sha `65b78a98bdea1bf2628f` / size 3055318 / BOM True / CRLF 49407 / 裸 LF 0 / py_compile OK / ast.parse OK。
- `region_analyzer.py`：本轮未改，sha `a67008a120f9dcf816b0` / size 1718595 / 无 BOM / CRLF 27546。

## 归档

`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round60/`
（OUTCOME.md）

起始 HEAD `246369b6`（Round 59 记录）。
