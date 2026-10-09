# Round 12 票面（从 round 11 的实测残余直接接续）

残余基线（round 11 封表，勿改动口径）：**6580/6617 单元（99.4408 %）/ 387 402 文件 / 15 文件 37 单元**，
判据尺 `scripts/pyc_verify.py`，四硬门 0。轮次规则不变：一张票只碰**一个机制**；先 FIX/DIAG 文档后施工；
只落地「有具名单元翻正且零回归」的补丁；零翻正逐字节回退；每次落地后跑满 402 门；命令 ≤300 s；
派子代理前先本地提交；每轮提交并 push。

## 前置状态（round 11 第二日已把三条轴的「不可用信号」钉死，别再重复）

1. 链首放宽族（blanket / J-gate / J+F-gate 三形）：一律 `bar +1` 单元换 `quote load_bars_from_hundsun −1` 单元，
   净 0 单元 0 文件；无副作用普查证明 bar 的 @34 与 hundsun 的受损头块在可测 CFG 事实上不可分
   → 见 `rounds/round11/DIAG_B139C_*.md` §4。重启需要**新的输入面**，不是第三条放宽。
2. handlers `@404`：父臂确实认领它（`IfRegion@0.then_blocks=[90,408,404]`），分支也执行，
   但 `_generate_block_statements` 返回空 ⇒ 属**隐式尾声拒绝**族（`#15`），与
   `query_strategy_id` / `query_trade_strategy_info` / `filter_desicion` / `check_frequency` /
   `get_individual_data` 同族。见 `rounds/round11/LEDGER_R11_DAY2.md` §B146。
3. 「区域从未生成 ⇒ 重派发其入口」在四条形下全部失败（quotation 153→137 两次、惰性一次、
   evt 产物 20555→5423 一次）：`_generated_regions` / `generated_blocks` / `generated_offsets`
   都不能区分「已发但不登记区域」与「从未发」。见 `rounds/round11/DIAG_B153_*.md` §3。

## T12-01（前置测量，允许纯读数票，不许动 core）

建立可判别的「**已发射区域入口**」台账：读 `_loop_generate_while` / `_loop_generate_for` 内对
`region.body_blocks` 的逐块消费点（候选 `region_ast_generator.py:8291`、`:7538`、`:7766`），
用**自证惰性**探针（只读局部量 + `start_offset`，跑完与封存产物逐字节比对）回答：

* 兄弟臂子区域经这条路径发射时，**有没有**任何地方记下它的入口偏移？
* 若没有：记录点应在何处（必须与 `generated_blocks.add(block)` 同处，避免第二真相源）？
* evt 的 `@7972` 与 quotation 16 个回归单元在「谁发射了它」上的**可分事实**是什么？

产出即 T12-02 的判据输入；不得在这张票里顺手改发射行为。

## T12-02（依赖 T12-01）`realtime_event_source` 整文件翻转候选

12/13，唯一失败单元 `<module>.RealtimeEventSource.clock_worker`，缺陷三形同单元：
110 指令 `if persist_flag is not False:` 体不发（@7972 入口未派发）＋ 17 指令块被搬到循环之后
＋ 3 处目标差。**只解决第一形**即可能翻正该单元，但必须逐形读回，不许把搬形记成本票收益。
判据必须以 T12-01 的台账为输入；放行条件必须排除「被兄弟区域以角色字段认领」的块
（分支探针实测一次放行命中 3 块，其中含健康单元 `TWHThreadRotatingFileHandler._target` 的 `@780`）。

## T12-03（独立）隐式尾声族：`#15` 的共用尾身份

具名单元：`handlers.TWHThreadController._target`(+2)、`trade_info_utils.query_strategy_id`(+1)、
`trade_info_utils.query_trade_strategy_info`(净 0 ⇒ 缺陷仍在)、`wizard_quant_api.filter_desicion`(−2)。
入口点：`_generate_block_statements` 对 `LOAD_CONST None; RETURN_VALUE` 的拒绝路径
（候选 `has_trailing_return_none`、`_is_trailing_return_none_statement`、
`_r8_b121_implicit_tail_landing_sinks`），以及「同一块在循环收尾扫处返回 1 条语句、
在父臂处返回空」的上下文差（`self._current_loop` / 区域标志 / `generated_offsets` 三选一）。
最优收益：handlers 翻正 1 文件；tiu/wqa 只进单元不翻文件，须在票面写清。

## T12-04（独立，收益最高但风险最高）`matcher` 三形同单元

16/17，唯一失败单元 `<module>.DefaultMatcher.match`。oracle `m_or_full.py` 实测 **17/17**，
目标文本逐行钉死在 `rounds/round11/DIAG_B138_*.md` §Task2；需要同时闭合
or-fold（`@1382`）、guard-fold（`@1910`）、被吞的 `@2164` 十指令测试三形。
单形不得开票（`m_or_i/ii/iii` 全部实测 16/17）。

## 排队中（未派，维持 round 10 票面）

`#21 <genexpr>` 下标操作数链、`#22 order_api` 被吞条件日志 + and/or 三元操作数链、
`#23` 函数内 import 丢失（4 处复制的硬编码 lookahead，窗口不一致 `+3/+3/+4`）、
`#24` f-string 片段拼入外来标识符、`#16`(B126) 归档补丁作为 `trade_live_broker` 三单元的共要件。

## 验收（全票统一）

`python -X utf8 pycdc.py <pyc> -o <scratch>`（先删产物）→ `scripts/pyc_verify.py single`；
残余名单以 `rounds/round11/RESIDUAL_R11.md` 的**单元名**为准（quotation 153/153、
`jq_trans_module` 65/65、small34 ≥1531/1568、anchor 名单 454/454 为哨兵）；
七套 pytest 与封表同名同数（2 failed / 280 passed / 2 xpassed）；
零翻正 ⇒ 逐字节回退并登记为本轮证伪臂。

## T12-02 施工尝试记录（未落地，工具教训先记）

按 §5 的窄道装过一版候选（台账 helper `_r164_note_emitted` + 出口边判据
`_r164_sits_on_foreign_loop_exit` + 臂循环内一处放行），**没有取得读数**：安装脚本用
「字节锚点 + 固定 `\r\n` 结尾」写 `region_ast_generator.py`，而该文件是 **混合行尾**，
于是 `b[:_P] + ADM + b[_P+len(CHK):]` 从一条注释的中部切断，产出
`SyntaxError: invalid character '」' (line 25146)`，三个文件的 decompile 全部报同一异常。
镜像随后已复原（`971df5e2c9cd7d0a` + `e926a54f17753b33`，仓库 `core/`、`site-packages/` 0 项改动）。
下一张票的施工规矩（照此做，别再花轮次在管道上）：
1. 插入必须**按物理行**做：`io.BytesIO(bytes).readlines()` 切行，找到唯一含锚点子串的那一行，
   用**那一行自身的结尾**（`\r\n` 或 `\n`）生成新行；禁止整文件统一换行、也禁止按字节偏移切文件。
2. 每次插入后**立刻**重新搜索下一个锚点（前面的插入会使旧偏移失效——本次就是这么坏的）。
3. 写盘后先 `py_compile`，再跑一个最小产物（quotation）与封存产物逐字节比对；
   产物异常（体积骤降 / GEN_FAIL）即说明改动污染了语法或语义，先回退再谈判据。
4. 候选判据本身仍按 §5：台账记入口偏移（`_emitted_entry_offsets`，单一 helper 两处共用），
   放行面限定在「入口块 ∧ 入口未记 ∧ 前驱是**另一条**循环的 back_edge_block 或以 FOR_ITER 结尾」，
   必测反例是 quotation `get_eps` 的 @994（已被直连路径发过）与两处同入口重复 LoopRegion。
