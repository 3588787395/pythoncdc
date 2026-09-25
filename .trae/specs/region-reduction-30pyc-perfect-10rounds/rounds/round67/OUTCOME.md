# Round 67 — OUTCOME

起始 HEAD = Round 66 记录提交（`f972bd3c` 之后的 R66 收尾）。本轮把 R66 落地态（官方尺 5746 / 5698 / 99.16%，
ok 386、partial 16）推进到 **5746 / 5701 / 99.22%，ok 387、partial 15、failed 0**。
原始读数与判定全部在 `logs/EVIDENCE.md`（A–G）与 `logs/gate/`、`logs/dump/`。

## 1. 本轮形态

用户 mandate：把剩余 partial **全部**分给并行子代理（不许手挑单一靶），再由中心集中验证与回退；
每轮至少把一支 pyc 修到完全 OK，再验 quotation，再批量回归；所有命令 <300 秒；门禁严格串行；
每轮提交并 push。

- 16 支 partial 按 `max(严格缺陷, 官方 gap)` 贪心均衡分 **6 批**、每批 ≤3 支（R66 教训：诊断代理死在
  150 轮上限，靶支数是主要开销），由 6 个**只读**诊断代理在各自私有工作区并行诊断；
  402 全量扫描归中心，brief 里明令禁止代理跑。
- diag1 返回后另派两名**实现**代理：`fix1`（把 diag1 被拒的 J1 收窄成同层判据）、
  `fix2`（把 diag6 已证根因但落在**第三个 core 文件**的缺陷实现出来）。诊断方交判据草案与失败读数，
  实现方只负责收窄与过门——不允许同一代理既诊断又落地。
- **本轮把可落地文件集从 2 个扩到 3 个 core 文件**（新增 `core/cfg/comprehension_generator.py`），
  并同步扩了仪器白名单（`h62.py` L49、`mbuild67.py` L24、`land67.py` 落地断言）。
  理由不是偏好，是实测：diag6 证得一条双尺皆红、根因明确、有 9 行合成复现的缺陷
  （`_detect_comp_ternary` 在**第一条** forward 条件跳转就 `break`，丢掉共享同一假出口的第二条跳转），
  它不在原两个文件里 ⇒ 白名单本身挡住了一支可修的真缺陷。扩集后该判据仍受同一套门禁约束。
- 集中验证采纳 4 件、回退 5 件（E 节逐条读数）；两步制的 diag5 成对落地。

## 2. 修到完全 OK 的 pyc（mandate：至少一支）

**`site-packages/IQData/utils/common_func.pyc`：官方 23/24 → 24/24 100.00%，严格 27/27 全一致**，
`missing_in_decomp []`、`extra_in_decomp []`，索引条目 `partial → ok`。
闭掉的缺陷函数是 `handle_exrights`（orig 276 / decomp 268），由 diag2 的 or-chain 尾段判据修好——
diag2 同时更正了中心轮初的误判：它**不是**位移族，真实缺陷是短路链第三操作数丢失 + 块 14 被当作链成员跳过而孤立。

同一轮另有两支各前进 1 个函数（未达全清）：`wizard_quant_api` 51→52（`calculate_di` 全对齐）、
`trade_live_broker` 107→108（`get_all_orders` 消失）。

## 3. 落地集（m67g：3 个文件、8 处编辑、+322 行）

| 文件 | 落地字节 | 编辑 |
|---|---|---|
| `core/cfg/region_ast_generator.py` | 3 153 249 B，sha256 `f712bc20d7ad44542e18…`，BOM **有**，CRLF 50 782，裸 LF **0** | 5 edits +156 |
| `core/cfg/region_analyzer.py` | 1 742 308 B，sha256 `af8cc88b9f89779b3ef0…`，无 BOM，CRLF 27 873，裸 LF 0 | 2 edits +110 |
| `core/cfg/comprehension_generator.py` | 108 192 B，sha256 `be5490c1118c7199fe0a…`，无 BOM，CRLF 2 016，裸 LF 0 | 1 edit +56 |

三支 `py_compile` + `ast.parse` 均 OK；`landproof mirr_m67g` = 33 core 文件 **same=33 diff=0**；
`land67.py land --apply` 断言「spec 重放 == 实测镜像字节」逐文件通过，产物与测量镜像逐字节相同。
行号为最终落地字节上的标记，三要素注释（识别条件 / 归约方式 / AST 映射）写入识别方法：

1. **analyzer L16452 `[R67-diag2 C1]`** — 短路链「负极性末段」补全：`BoolOpRegion` 的 or-run 尾段若自身
   以负极性条件跳转收尾且假出口即本区域汇合块，则把该末段作为操作数补回链上（只读本 run 的块序列与
   本区域 `merge_block`）。消费者：`common_func::handle_exrights`（官方 +1 且全清）。
2. **analyzer L21094 `[R67-diag5 (d')]`** — 值语境链式比较三元头块判据 (d) 的放宽：不再「块内任何位置有
   `STORE_*`/`POP_TOP` ⇒ 整体拒绝」，而是按该块**自身栈深归零点**划出表达式段，只有表达式段内含
   `STORE_*`/`POP_TOP` 才拒绝；栈效应不可得或下溢 ⇒ 退回落地行为（保守）。
   必须**局部 `import dis`**——`region_analyzer.py` 没有模块级 `import dis`，否则 NameError 被上层宽 except 吞掉、
   产物静默退化（实测 `[36,28,0,29]`）。与第 6 条**成对**才生效。
3. **generator L19900 + L25871 `[R67-diag4-A]`** — helper `_handler_backedge_is_explicit_continue`：
   `TryExceptRegion` 的 handler body 以**纯回边块**收尾 ⇒ 源码是显式 `continue`，发射 `Continue` 而非空 `Pass`/丢弃。
   官方尺中性，严格尺 `realtime_event_source` 10/12→11/12（`get_one_event` 缺陷消失）。
4. **generator L21970 `[R67-fix1 J3]`** — 循环发射中不得认领「自身 `merge_block`/`exit` 皆为空」的顶层兄弟区域；
   五个条件全读本帧 `blocks` 实参与 `_region` 自身字段。反例 `quotation::get_trend`（`mb=220 x=220`）
   由第 (5) 条挡住 ⇒ 金丝雀 sha 逐字节不变。消费者：`trade_live_broker::get_all_orders`（官方 +1）。
5. **generator L34887/L34889 `[R67-diag5]`** — helper `_r67_split_cc_ternary_stmt_prefix`：Phase-7-D 的
   值语境链式比较三元分支（`chained_compare_ops>=2 ∧ chained_compare_blocks`）此前用
   `_build_chained_compare_from_region_data` **直接从区域数据**建 `Compare`，整体绕开了普通三元 `else` 分支里的
   前导语句扫描 ⇒ 头块内**已完结**的前导语句无人发射。本条复用 `_split_block_condition_prefix`
   （与 Assert / 旋转 while / R63-b3 **同一条**栈深划界）+ `_build_statements_from_instructions` +
   既有 `results = list(pre_stmts)` 发射通道。独立见证：`w2/w3/w4/w5/c6` 五支（其头块都不是 CFG 入口块，
   与判据 (a)/(d) 无关）——即这是一条**此前无人负责**的语句丢失族，不是 v6 的附属步骤。
6. **comprehension_generator L1620/L1641/L1702/L1718 `[R67-fix2]`** — helper `_r67_boolop_chain_end`：
   聚合推导式内的三元 `A if (A > 0 and B > 0) else 0`，CPython 把每个 `and` 操作数编成一条
   **共享同一假出口**的 forward 条件跳转；原实现在第一条跳转处 `break` ⇒ 条件区只含第一个合取项，
   产物降级为 `A if A > 0 else 0`（丢 24 条指令）。本条把条件区延伸到链上最后一条共享假出口跳转；
   链不纯（区间内出现 BACKWARD 条件跳转或异目标跳转）⇒ 返回 `None` 保守退回 R10 路径。
   消费者：`wizard_quant_api::get_DMI.calculate_di`（官方 51→52、严格 52/56→53/56）。

**禁止形态核对**：8 处编辑全部只读本区域/本块自身字段；无 `region.entry in r.blocks` 型跨区域跨层次包含、
无函数名/文件名片段/偏移/阈值启发、无新增 `self` 状态、无按名字白名单。

## 4. 串行门禁（严格串行，逐条见 `logs/gate/`）

| 门禁 | 读数 |
|---|---|
| G1 完全 OK 靶 | `common_func` 官方 **24/24 100.00%**（missing/extra 皆空）+ 严格 **27/27**、文件级全部一致 |
| G2 金丝雀 quotation | 官方 **143/143**；严格 **148/150**，缺陷集逐字为 `change_his_to_forward #250`、`get_trend #10`（**逐字未变**）|
| G2 其余金丝雀 | `market_time` 10/10 + 严格 10/10；`IQCommon/util/datetime_func` 26/26 + 26/26；`IQData/utils/datetime_func` 25/25 + 25/25；4 支产物 sha 逐字节不变 |
| G3 批量 | `batch --index pyc_index.json --all --round 67` → **402 verified / 0 failed**、ok 387、partial 15，日志内 `FAIL/Traceback/Error` 0 命中 |
| G4 `stats` | **5746 funcs / 5701 matched / 99.22%**（轮初 5698 / 99.16%）⇒ matched **+3**、完全匹配文件 **386→387** |
| G4′ 严格尺（已发布产物） | **659/727**（轮初 655/727、缺陷函数 72→**68**）；每一支 `mirror-sha …=measured` ⇒ 出货字节 == 被测字节 |
| G5 索引审计 | 402→402 条目、added=0 removed=0、key-shape diffs=0、round-stamp-only=399、**substantive=3 且全为改善**；写回后与 G3/G4/402 sweep 逐支相同（per-file diff 0）|
| G5′ 产物 blast | `identical=396 changed=6 unresolved=0`，改动集**恰等于** IMPROVED(3)+MOVED(3)；Σ|Δ| **328→296**；未手改任何 `*OK.py` |
| G6 电池 | 31 项 115/127→**116/127**（`r66d3_pred` 2/3→3/3）；公开 45 项（含本轮 14 支新复现）161/200→**174/200**、缺陷函数 39→**26**、8 项变好、**worse-than-landed=0**、errors=0 |

G6 的「landed 列」在落地后与候选列同字节（两次读数逐行相同），故另建 `center/mirr_r66`
（HEAD blob + LF→CRLF 复原，两支 R66 指纹大小+sha256 命中 R66 提交记录）作**真基线列**，
脚本 `mkmirr_r66.py`、日志 `G6_battery_r66_vs_m67g.txt`。

**附带改善（官方尺逐支）**：`api_base::get_history_df` 指令缺口 缺 23 → 缺 2（1742/1719→1742/1740，
文件级仍红）；严格尺 FIXED 6 条：`calculate_di`、`get_history_df`、`handle_exrights`、
`get_one_event`、`get_all_orders`、`run_tick_transform target_diff #135`；
NEW 2 条均为同一函数「改善后仍红」或「同一条缺陷换位置」，无新增缺陷函数。

## 5. 六批 + 两实现代理的判定

| 批 | 名下靶支 | 交付 | 判定 |
|---|---|---|---|
| diag1 | `trade_live_broker`（1 支） | `cand_r67_j1` | **拒**（金丝雀 sha 移开 + 靶支不利）；其「J1 使靶支 ERR」被复测更正 |
| diag1b(fix1) | 同上 | `j3`（5 条件同层收窄） | **采纳**：官方 +1（trade_live_broker 107→108）、电池 SAME=31、金丝雀 4 sha 全同 |
| diag2 | common_func 等 3 支 | `c1` | **采纳**：官方 +1 且把 common_func 修到 **24/24**；更正中心轮初对 `handle_exrights` 的位移误判 |
| diag3 | flyAccount 等 3 支 | `d3c1` | **拒**（Σ|Δ| 不变：过冲 7 翻成等量欠缺 7）；判据与注释形态留档 |
| diag4 | realtime_event_source 等 3 支 | `hc`（2 edits） | **采纳**：官方中性、严格 10/12→11/12；更正仪器三处 |
| diag5 | real_quote / order_api / scheduler | `ccp_final`（generator 2 edits）+ `dsplit_analyzer` | **成对采纳**：单改 analyzer 丢语句、单改生成器对 landed 的 v6 惰性（两条都是实测）⇒ 落地次序「生成器先行 + analyzer 后随」在本合并集内一次完成；`r66d3_pred` 2/3→3/3、合成 1/5→5/5 |
| diag6 | wizard / risk_calculation / fly.logger | `r67d6w1`（拒）+ 第三条文件的根因证明 | **W1 拒**（两支同步崩塌 113→41、41→32）；根因转交 **fix2** |
| fix2 | —（实现代理） | `cand_r67_comptern_boolop`（1 edit） | **采纳**：wizard 51→52、严格 52/56→53/56、电池 SAME=31、金丝雀 4 sha 全同、16 支 REG=0。未自留 FACTS/ANALYSIS，其分析由中心按其 dump 补写（EVIDENCE F.1）|

## 6. 残余 15 支 partial 的家族归属（gap 合计 45 个函数）

| 家族 | 涉及 | 已知证据 |
|---|---|---|
| **位移 / 线性化通道**（整段语句被搬到函数尾，零语句增减） | `real_quote`（4）、`klinedata`、`matcher`、`fileio_utils`、`trade_info_utils`、`quote`（部分） | diag5 归一化 hunk 表 + [[project-r66-displacement-family-lead]]、[[project-r64-matcher-displacement-lead]]：counts 已相等 ⇒ 查**顺序**而非归属 |
| **R50 kwarg 槽位 bail**（臂体被空化成 `pass`） | `order_api`（2）、`flyAccount`（2） | `_try_build_ternary_kwarg_call`（落地 L43162，唯一调用 L38156）；`base_order` 的严格 `target_diff` 是常量↔LOAD 消费点错位 |
| **try/loop-exit JUMP_FORWARD + IMPORT_FROM-as-value** | `risk_calculation/__init__`（2）、`wizard_quant_api`（1：`params_analysis`） | diag6：三个签名纠缠（`JUMP_FORWARD`↔`LOAD_CONST None/RETURN_VALUE` 互换、`IMPORT_FROM` 被物化成 `STORE_NAME`+`if`、回边被改成 forward）；见 [[project-r47-try-body-return-guard]] 禁令 |
| **cellvar / 闭包变量降级**（区域层之外） | `scheduler`（2） | diag5 遵守禁令未攻 |
| **发射次序（while-True 头块混合 store+条件跳转）** | `fly/logger`（1：`write_logging_thread`） | diag6 已复现到 14 行；需生成器侧「重发头块前缀去重」配套，单侧判据实测同步崩塌 |

## 7. 下一轮（R68）线索

1. **位移族是最大单一矿**（约 12 个 gap 函数）：`real_quote` 四支 + `klinedata` + `matcher::match` 共享
   「30/35 条整段搬到函数尾」。一处生成器重排/线性化通道可修多支；分头做判据必然取巧。
   起点：产物尾部的整段插入点与 `IPO_*`/`_loop_build_if_with_exit_branches`（落地 L10495）的调度顺序。
2. **`diag6 W1` 的配套条件**：抑制 `_should_skip_block_for_if_region` 对 while-True 头块的跳过已实测能重新调度
   `IfRegion@368`，但循环体会**重发头块前缀语句**⇒ 必须先有生成器侧前缀去重，再谈该判据；
   spec 与读数留在 `batches/diag6/specs/cand_r67_whiletrue_headif.json`。
3. **`diag1b b1` 的根因可复用**：回收到的汇合点若同时承载消费者与其后语句，需要「首个消费者之后」的
   划界；`_mb_first_store_idx`（L21785-21794）只会按 `STORE_*` 切 ⇒ 与本轮 diag5 的栈深归零划界是同一形态，
   可考虑把 `_split_block_condition_prefix` 提为该处的公共依赖。
4. **尺子覆盖问题（真实语义反转，官方尺看不见）**：`fly/logger::SafeFileHandler.check_baseFilename`
   官方 34/34 PASS，严格 `target_diff #14` 抓到 `not` 从单个操作数被推到整个 `BoolOp`。
   修法应在**语句条件语境**的 or-chain 折叠处（`_generate_if` / `_build_ternary_boolop_condition` L33937 路径）
   保持极性归属；同时值得给官方尺加一条「jump-target 常量身份」检查，否则这类反转永远计分通过。
5. **`wizard_quant_api` 只差 1**：`params_analysis` 属 try-tail JUMP_FORWARD 族（3 个纠缠 hunk，含丢失的
   `float(value_params)` 组）——禁令：不得把 try 尾 `Expr` 改写成带值的 `Return`（见 [[project-r47-try-body-return-guard]]）。
6. **技术债**：generator 内残留的 `_os_dbg_*` 调试导入仍需清理（见 [[project-r65-debug-import-cleanup]]，
   清理是 402 惰性的噪声移除，不得当提速或收益报告）。
7. **第三个 core 文件已进白名单**：`comprehension_generator.py` 的其余消费者
   （`_detect_comp_ternary` 的 filter/ternary 共存路径、`merge_offset` 之后的 dict-comp value 段）
   本轮未触碰；诊断代理今后若在此文件发现根因，直接按同一门禁交 spec，不必再转中心扩集。
