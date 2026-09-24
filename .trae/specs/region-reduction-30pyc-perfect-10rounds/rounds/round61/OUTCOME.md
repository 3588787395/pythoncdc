# Round 61 OUTCOME — R57–R59 五支真回归收窄修复（回归修复轮）

## 内容

回归根因见 `D:\Temp\opencode\r61\FINDINGS.md`（arm 矩阵 + hunk 实证）。本轮只做**结构性质收窄**，不读名字/常量/绝对偏移/指令数；修改严格附加；中文注释「识别条件→归约方式→AST 映射」三段式；变量前缀 `_r61*`。

### GEN Fix1 收窄 — `_r61_is_pure_jump_stub` 合取（region_ast_generator ~L21352 + 模块级 helper L213）
- **识别条件**：R57 Fix1 的共享 break 跳过仅当 merge 剥噪声后（剔 RESUME/NOP/CACHE/EXTENDED_ARG）非空且全属 `{POP_TOP, JUMP_*}` 纯跳转桩。
- **归约方式**：`_r57b_skip_shared` 追加 `and _r61_is_pure_jump_stub(region.merge_block)`；真实条件 merge（LOAD_FAST+POP_JUMP 等）仍臂内发 Break。
- **AST 映射**：桩 merge 的 Break 由父层 post-if 发一次；否则 `stmts+=Break`。
- 证据：victim merge@404 非桩 → create_daily_stats 恢复；target merge@1298 POP_TOP+JUMP_FORWARD 桩 → order_entrust_info_handle 保持 ok。

### GEN Fix3 收窄 — In/NotIn Compare 头不 `_negate_expr`（region_ast_generator ~L17316–17321）
- **识别条件**：or 链 Fix3 分支命中后，`_part` 为 Compare 且 ops ∈ {In, NotIn, in, not in}。
- **归约方式**：跳过 `_negate_expr`（CONTAINS_OP arg 极性由跳转对偶吸收，再包 not 会翻 arg）；其余头保持否定。
- **AST 映射**：`BoolOp(or, [A, B])` 不额外包 `not` → 重编译 CONTAINS_OP arg 与 orig 一致。
- 证据：api_base get_history CONTAINS_OP 0/1 恢复；replace_utils 严格尺保持 9/9（Fix3 全关会掉到 8/9，已证伪）。

### ANA Fix2 收窄 — `_r58_fie` 纯跳转桩 + 后继 ∈ break_blocks（region_analyzer `_fie_succ_in_break`）
- **识别条件**：`_r58_fie` 剥噪声后为纯跳转桩，且其后继 ∈ 父循环 `break_blocks`。
- **归约方式**：否则置 `_r58_fie = None`，走旧 cleanup 剔除伪 else。
- **AST 映射**：victim 三支（check_python_code / stk_history_day_complex / create_sys_account）恢复；default_event_source 目标保持 ok。

### ANA R57-E 收窄 — merge ≠ loop header（region_analyzer call site）
- **识别条件**：`_merge_e is not None and merge is not getattr(_loop, 'header_block', None)`。
- **归约方式**：merge 即循环头时不做分支汇合回退。
- **AST 映射**：victim create_portfolio 恢复；trade function 目标保持 ok。

临时臂脚本：`D:\Temp\opencode\r61\{apply_gen_only,apply_helper_fix3,verify_official,verify_strict,combined_r61_verify,a2_r59_fix3_verify}.py`。

## 验证

| 尺 | 落地前（HEAD 索引） | 落地后 |
|---|---|---|
| 官方关键 9 支 | 4/9 partial（5 支回归） | **11/11 全 ok**（含 quotation/market_time 金丝雀） |
| replace_utils 严格 | 9/9（Fix3 全开会掉 8/9） | **9/9** |
| risk/trade/events 严格 | — | **15/15 / 71/71 / 14/14** |
| instance 严格 | 33/33 | **33/33** |

官方 single 复验（`verify_official.py`）：api_base 48/48、replace_utils 9/9、risk function 15/15、ptrade_broker 11/11、strategy_info 28/28、history_api 18/18、trade function 71/71、default_event_source 14/14、instance 32/32、quotation 143/143、market_time 10/10。

## 门禁与全量指标

- **真基线对照**（R60 `batch --all` 提交索引）：ok 374 / partial 28 / matched 5666 / 98.61%。
- **R61** `batch --all --round 61`：402 verified / **0 failed**；ok **374→380**（+6）、partial **28→22**（−6）、matched **5666→5674**（+8）、rate **98.61%→98.75%**；逐文件 **REGRESSIONS=0、IMPROVED=6**。
  - IMPROVED：risk function、ptrade_broker、strategy_info_utils、history_api、api_base（5 支回归修复）+ **finance.pyc**（23→24，顺带受益）。
  - 另 klinedata matched 41→42（仍 partial，非翻转）。
- **vs 真基线（R60 前诚实基线 ok 373/29/5665）**：ok +7、partial −7、matched +9（含 R60 instance +1）。
- **G7** stats：total 5746 / matched **5674** / **98.75%**。
- **金丝雀**：quotation strict **148/150** 缺陷集不变（change_his_to_forward/get_trend）+ bytecode **143/143**；market_time **10/10**；trade function **71/71**；default_event_source **14/14**。
- **严格尺注记**（官方已吸收、非本轮引入）：api_base get_history 严格仍 #39 跳转极性、ptrade create_portfolio/create_sys_account、history get_price —— 与 HEAD 真基线一致的既有严格缺陷集；本轮不扩大。
- ***OK.py**：`--all` 重生成产物，与官方尺一致，随索引提交。
- **pyc_index.json**：5 支回归 + finance `decompile_status=partial→ok`、`last_tested_round=61`；全量 402 条 round=61。

## 字节面（终值）

- `region_ast_generator.py`：sha `291d9baeb94322109a5a` / size 3057129 / BOM True / CRLF 49438 / 裸 LF 0 / py_compile OK / ast.parse OK
- `region_analyzer.py`：sha `eab9c782a0b646f52781` / size 1719972 / 无 BOM / CRLF 27568 / 裸 LF 0 / py_compile OK

## 归档

`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round61/`（本 OUTCOME.md）
研究证据：`D:\Temp\opencode\r61\`（FINDINGS.md、arms/、hunks/、head_single/、trees/）

起始 HEAD `4f462abf`（Round 60 记录）
