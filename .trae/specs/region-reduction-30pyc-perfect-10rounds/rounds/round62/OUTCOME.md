# Round 62 结果（OUTCOME）

起始 HEAD：`3eb41a78`（Round 61 记录）。本轮按「五批子代理并行诊断 → 主循环集中验证回退」执行；
子代理全部在 23:55 后静默（`ANALYSIS.md` 停在半成品，无结论返回），故验证与取舍全部由主循环完成。

## 1. 落地内容（唯一改动文件：`core/cfg/region_ast_generator.py`）

`region_analyzer.py` 本轮未改。文件字节：`sha256:20 b9778ee0130865d55888`、3 059 418 B、
CRLF 49 463、裸 LF 0、**BOM 保留**；`ast.parse` + `py_compile` 通过。
落地前（Fix1+Fix2 态）`fa0808ca3766b5150dcf` / 3 058 524 / CRLF 49 455；HEAD R61 为
`291d9baeb94322109a5a` / 3 057 129 / CRLF 49 438。

四处改动，每处均按「识别条件 / 归约方式 / AST 映射」三要素写入识别方法注释：

- **[R62 Fix1]** L34615-34628：`_r62_has_store_before_push_null` 的 STORE 集合补 `STORE_ATTR`、
  `STORE_SUBSCR`（原只认 `STORE_FAST/NAME/GLOBAL/DEREF`）。识别条件＝call preload 之前出现任意
  `STORE_*` ⇒ 前缀是独立语句；归约＝复位 `func_call_skip=0`，交下方 STORE 分支切进 `pre_stmts`；
  AST＝每条 STORE 归为独立 Assign，三元只拥有其后的条件表达式。
- **[R62 Fix2]** L35335-35352：`_r62_outer_is_independent_store`（`merge_context=='store'` 且
  `value_target` 已设）时跳过 chained-container 早触发。识别条件＝外层已是独立 store 赋值，内层
  `container_type` 只来自 merge 块后续无关 `BUILD_*`（真容器链外层 `value_target` 为 None）；
  归约＝外层走 store 路径、内层独立生成；AST＝两条独立 Assign 而非错误 `Tuple(IfExp, IfExp)`。
- **[R62 Fix3]**（原 L34715 块）**已回退，未落地**。逐 fix 反向着陆实测（arm `rev_fix1/2/3/all`，
  由 `git cat-file` 机械派生的反向 spec）：Fix3 在全 402 语料上的唯一效应是把
  `IQCommon/api/klinedata.pyc` 从 42/45 打到 40/45，纯负债。回退 spec 自带自证：全部 hunk 反向
  应用后逐字节等于 HEAD。
- **[R62 Fix4]** L4584-4606：把 `[R102 fix]` 的 for 前缀写回抑制**只作用于首条**（`enumerate` +
  `_r62_pi == 0` 同时门控 Name 与 Attribute 两个 `continue` 分支）。

## 2. 靶文件与根因

`site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc :: <module>.DefaultLogger.setup`
（R56 遗留三大损失之一）：

| 状态 | 官方尺 | `setup` orig/decomp/true_diffs |
|---|---|---|
| HEAD R61 | 9/10 | 320 / 253 / 293 |
| +Fix1+Fix2 | 9/10 | 320 / 313 / 199 |
| +Fix4（本轮落地） | **10/10** | 缺陷列表为空 |

严格尺对落地态复核：**10/10、文件级 1/1、真缺陷 0 ⇒ 双尺全清**（该文件原在 22 支 partial 名单中）。
恢复的唯一语句是 `info_backtest_sys_handler = LogEngine.add_async(info_backtest_sys_handler)`
（两份产物逐行 diff 仅此一条 `>`，`add_async` 计数 5→6）。

根因：`[R102]` 以「目标名 ∈ 子 TernaryRegion 的 `value_target`」通配删除 for_iter_setup 前缀语句，
而 join 块里同名可出现多条独立语句 ⇒ 把 For 区域自己的成员语句一起吞掉。区域归约读法：子区域在父层
已是单个抽象节点，父层不得吞并成员语句；只有**前缀首条**才可能是子区域的 merge 写回。
证据链：`dd/witness_r102.py`、`dd/shape_search_r102.py`、`dd/trace_any.py`，形状 A/B/C/D/E + 控制。

## 3. 门禁（严格串行，均单变量）

- 电池（六支见证，landed vs f4）：`w_B_two_such_calls` 1/2→**2/2**、`w_C_attr_then_reassign`
  1/2→**2/2**；负控 `w_D_plain_no_ternary`、R102 控制 `r62f_r102name` 保持 2/2 且产物逐字节相同；
  `w_A`/`w_E` 两臂产物逐字节相同（Fix4 对它们中性，非回退）。
- 全量 A/B（镜像臂，非侵入）：`landed402b`(fa0808ca) vs `f4_402` ⇒
  matched 5674→**5675**、clean 380→**381**、**REGRESSION=0 IMPROVED=1 MOVED=0 SAME=401**；
  轮次合计 HEAD→R62 同为此数。
- 逐字节产物核对：`build_landed` vs `build_f4` 共 408 份 `*OK.py`，**405 相同 / 3 变**
  （靶文件 + `w_B` + `w_C`）；`[R102]` 守卫集 8 支（`fly/simtradding/*` 6 支 +
  `fly/data/quotation` + `request_data_transform`）全部原样。
- G1 单文件：`pyc_batch_verify.py single` 靶 pyc ⇒ `decompile_status ok`、**10/10、100.00%**、
  missing/extra 均空，`__init__OK.py` 由工具生成（未手工改动任何生成文件）。
- G2 金丝雀：`fly/data/quotation.pyc` 官方 **143/143**；严格 **148/150**，缺陷集合逐字不变
  （`change_his_to_forward` #250、`get_trend` #10）——与 R58-61 完全一致。
- G3 批量回归：`batch --index pyc_index.json --all --round 62` ⇒ **402 verified / 0 failed**、
  ok 381、partial 21。
- G4 `stats`：**5746 functions / 5675 matched / 98.76%**（R61 为 5674 / 98.75%）。
- 索引核对：`pyc_index.json` 相对 HEAD 逐行差 812 行 ＝ 402×2 轮次戳 ＋ 靶条目 4 字段
  （`decompile_status`/`bytecode_match_rate`/`matched_functions`/`ok_py_generated`）；
  **除轮次戳外仅靶条目变化**；纯 CRLF 4553 行、裸 LF 0、无 BOM。全量重跑仅 1 支 `*OK.py` 变化
  （＝靶文件），工作树只有 3 个 `M`。

## 4. 集中验证回退（五批产出）

五个 `diag*/` 工作区最后写入时间均为 23:55，`ANALYSIS.md` 是未完成的中途记录，未收到任何 agent 结论，
因此把它们留下的两份机器可读 spec 按**各自点名的见证**实测（臂基线＝Fix4 落地态，镜像先过语法检查）：

- `diag1/specs/cand_fstail2.json`（生成器，链式 f-string「TOS 存活」判据 + 委托
  `_try_build_ternary_merge_consumer_expr`）：`trade_live_broker.pyc` 104/119 → 104/119，
  且**逐函数元组零变化** —— 对它诊断的 `fund_transfer`（123/91）完全无效 ⇒ **INERT，不落地**。
- `diag5/specs/cand_fixa.json`（分析器，把 `POP_TOP` 视为 merge 块首个栈顶消费者）：
  `fly/logger.pyc` 28/30 → 28/30，同样零逐函数变化 ⇒ **INERT，不落地**。
- `diag2/3/4` 未产出 spec。

两支柱未删除（归档于 `specs/`），其目标函数探针原始数据（`diag1/logs/ft.probe.txt`、`diag5/logs`）有效；
结论是：两位作者推断的机制都不是生效机制，续做须先换判据而不是换阈值。

## 5. 遗留与移交（Round 63）

- `w_A`/`w_E` 形状：`[R102]` 过滤在「同一目标名有多条前缀语句」时仍会误吞非写回语句
  （w_A 丢 `second = wrap_async(second)`）。名字判据本身是错的，正解应是栈跨度/语句终结符判据；
  语料内无此形状，故本轮无对应官方尺收益，属真缺陷。
- 剩余 21 支 partial、三大损失中的 `get_kline_local -78`、`get_TradeMode_trades -90`、
  线 B 伪造尾随 `continue`、`base_order [target_diff] #136` 等清单沿用 R56/R61 交接。
- `fly/logger.pyc :: logging_process`（99/98、true=54）、`trade_live_broker.pyc` 15 支不匹配函数
  （`fund_transfer` −32、`market_fund_transfer` −27 同族）仍是最大单文件损失。
- 归档：`EVIDENCE.md` A-K 全文、`specs/`、`logs/`、五批原始工作区保留在
  `D:/Temp/opencode/r62gate/`；本轮目录含 `batches/`（五批 ANALYSIS+FACTS+targets）、
  `specs/`（Fix4 判据 + 两支 INERT 候选 + Fix3 回退 spec）、`logs/`（门禁 A/B 与见证计数）。
