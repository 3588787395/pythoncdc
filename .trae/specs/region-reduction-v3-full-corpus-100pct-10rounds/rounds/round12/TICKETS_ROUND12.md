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

## T12-02 第二次施工：装配成功但放行零命中，并更正我先前写错的行尾结论

按 §规矩重做装配（物理行插入 + 沿用该行结尾），脚本 `D:/Temp/r141/t1202_rig.py`
（产物字节 `05b7e6f38108980d`，`compile()` 通过）。读数：
`realtime_event_source` 仍 **12/13**、产物 `20555` 字节 **SAME_as_HEAD**；
`handlers` 仍 29/30、`9093` 字节 SAME_as_HEAD ⇒ **放行分支一次也没命中**。

先更正我自己写错的事实（先前提交 `619f9525` 把它当成结论，是错的）：
`region_ast_generator.py` **不是混合行尾**——本次逐行统计：59112 行全部以 `\r\n` 结尾。
上一轮 `SyntaxError: invalid character '」' (line 25146)` 的真因是
**旧字节偏移复用**：我在一次插入之后仍用插入前算好的 `_P` 做切片，切点落在注释中部。
所以 §规矩里「按物理行插入并沿用该行自身结尾」是对的，但把它归因于混合行尾是错的；
正确的必要性表述是：**任何一次插入之后都必须重新搜索锚点**，不得复用旧偏移。
另记一条同类失误：`body_of(line)` 无条件去掉最后一个字符，
使没有结尾换行的插入块丢掉末字符（`self._r164_note_emitted(region` 少了 `)`），
判据应是「只有真的以 `\r\n` 或 `\n` 结尾才剥掉」。

下一步（不是再叠判据，而是先读命中路径）：`@7972` 没走到我放行的那道闸，
说明在它之前还有别的 `continue`（同方法内 `if … in self.generated_blocks` 形式有 5 处，
另有 anchor/子区域入口/`_fis_skip_blocks`/`_loop_entry_generate` 等分支），
或者 `_emitted_entry_offsets` 已被**同入口的另一个区域对象**写入（本仓已两处实测到
同入口重复区域）。下一票第一件事是用自证惰性的探针打印
「`@7972` 在 `_process_if_blocks` 循环里到底走到第几条 `continue`、
`_emitted_entry_offsets` 当时是否含 7972」，再决定放行点与守卫。
镜像已复原 `971df5e2c9cd7d0a` + `e926a54f17753b33`，仓库 `core/`、`site-packages/` 0 项改动。

## T12-03 读数更正：放行**确实执行了**，丢语句发生在 `_process_if_blocks` 返回之后

前一段我写「放行分支一次也没命中」——那是**假的**：我以为装上了诊断打印，实际那次替换没命中，
跑的还是无打印版，于是把「产物不变」误读成「没触发」。直接按物理行插入打印后拿到真读数
（镜像 `core/cfg/region_ast_generator.py`，`[R165]`）：

```
[R165] block@7972 in_ledger=False edge=True entry_regions=1 generating=True     (第一次访问)
[R165] block@8170 in_ledger=False edge=False entry_regions=0
[R165] block@7972 in_ledger=True  edge=True entry_regions=1                     (第二次、第三次访问)
```

⇒ 三个条件全满足、分支进入、`_generate_region(IfRegion@7972)` 被调用（第二次访问时入口偏移已出现在
台账里，正说明第一次确实派发了），**而产物仍与封存产物逐字节相同（20555）**。
同一条判据在 quotation 上零改动（153/153、产物 SAME_as_HEAD）⇒ 放行面本身是干净的，
问题在**下游**：`_process_if_blocks` 为 reg@7582 产出的语句列表被调用方覆盖或丢弃。

所以下一票的施工顺序改成（不要再改放行判据）：
1. 用行级追踪（已证明只读 `f_locals['block']`，不改产物）打印 reg@7582 那次调用
   **返回之后**调用方拿到的语句数与随后对 `then`/`orelse` 的赋值；
   候选调用方：`_generate_if` 主体、`_if_generate_elif_chain`、`_if_generate_branch_stmts`
   （`region_ast_generator.py:27593` 一带已是转发层，真正的覆盖点在 `_generate_if` 里）。
2. 只有确认「结果被覆盖」之后，才谈改那一处的合成逻辑；放行判据（台账 + 出口边）保持现状。
3. 管道教训两条（都已进记忆）：装配脚本的**替换字符串必须验证命中数**，
   没命中却继续跑会给出「假阴性读数」；探针插入用物理行 + 该行自身结尾，
   插入前断言唯一命中，插完立刻 `py_compile`，失败即从仓库字节复原镜像（本次照做，
   镜像已复原 `971df5e2c9cd7d0a` + `e926a54f17753b33`，仓库 0 项改动）。

## T12-05 / T12-06：认领点已找到并改到位，但仍逐字节不变——存在第二个写入者

写栈追踪（`t1209`，HEAD 字节、只在本进程把两个集合换成记录型子类，不改仓库文件）给出
`@7972` 在 HEAD 被登记的全部三次写入：

| 次序 | 写入行 | 调用链摘要 |
|---|---|---|
| 0 | `region_ast_generator.py:25236 self.generated_offsets.add(_nb.start_offset)` | `… _nr_ast = self._generate_region(_nr)` → `_if_generate_then_branch` → `_process_if_blocks(then)` |
| 1 | 同上 `:25236` | `_if_generate_full_elif_chain` → `_if_generate_elif_chain` → `_process_if_blocks(region.elif_final_else, branch='else')` |
| 2 | `region_ast_generator.py:8462 handled = self._loop_dispatch_block(` ← `:9246 if self._loop_handle_child_region_entry(block, region, child_info, body_stmts):` | 循环体逐块消费路径 |

两次改动都已装到镜像并实测（每形都 `compile()`+`py_compile` 通过，产物与封存产物逐字节比对）：

* **T12-05** `a375d8be8c4043ad`：把认领豁免从「只在 `not _nr_ast`（让位）时跳过兄弟入口」
  扩成「兄弟入口只要没被渲染过就不认领」，台账 `_emitted_entry_offsets` 记在
  `_generate_region`/`_generate_if` **入口处** ⇒ evt `20555` SAME_as_HEAD、12/13；
  quotation 153/153、handlers 29/30 均 SAME_as_HEAD。
  ⇒ 该台账把「进入漏斗」当成了「已发语句」，语义错位（`_generate_region` 的 `finally`
  无论返回值是否为空都会记 id，同理入口记录过宽）。
* **T12-06** `0a0da79adf426623`：台账改成**只在 `_nr_ast` 非空处**记（唯一锚点对
  `discard(_nr_id)` + `if _nr_ast:` 配对断言命中数后插入），并同步放宽认领 ⇒
  三个文件产物**仍逐字节相同**，evt 仍 12/13。

⇒ 结论：**光放开 `:25236` 的认领不够**，因为还有第 2 个写入者（循环体路径
`:8462` / `:9246`）把同一个块登记掉；要让 `@7972` 走到发射，必须一并处理
`_loop_handle_child_region_entry` / `_loop_dispatch_block` 的登记语义，或把消费顺序改成
「先派发该入口区域、再让认领循环看到它」。下一票的起点因此不再是找判据，而是：

1. 读 `:9246`→`:8462` 这条链在 `@7972` 上做了什么（它 `handled` 返回真值吗？
   若返回真值却没发语句，就是同一类「吞而不发」，应在此处补；
   若返回假值，则登记发生在它之前，需按写入次序排序）。
2. 沿用已验证有效的记录型集合探针（`t1209`）逐次打印写入者与 `handled` 返回值。
3. 判据侧不再新增放宽条件：T12-05/06 的认领豁免语义是对的（原则 2/4，且 quotation
   153/153 零改动证明它不吞健康单元），保留它，另补循环路径。

装配管道本轮又踩实了三条，全部进记忆：替换/插入脚本必须断言**命中数**（我用 7 命中的
锚点跑了一次「假成功」，靠 assert 才没写坏文件；另一次替换未命中导致读数重复上一轮的假阴性）；
台账语义要区分「进入过渲染函数」与「真的产出了语句」；探针与候选混装会让结论错向。

## 写作者地图（截至 T12-06，供下一票直接用，不必重新推导）

`@7972`（clock_worker 里 `if persist_flag is not False:` 的入口块）在 HEAD 被登记三处；
两处已由 T12-05/06 的认领豁免放开（quotation/handlers 逐字节不变，说明放开是安全的），
第三处仍在循环体路径里，其代码形状是共通的：

```
region_ast_generator.py:13884 def _loop_handle_child_region_entry(...)   # 6+ 个分支
    _x_ast = self._generate_region(entry_region)      # Try/With/Try/Loop/Loop 各分支同形
    for b in entry_region.blocks: self.generated_blocks.add(b)   # 认领整块
    return True
region_ast_generator.py:8868  def _loop_dispatch_block(...)
    self.generated_blocks.add(block); self.generated_offsets.add(block.start_offset); return True
```

⇒ 关键待读问题（一次探针就能定）：`@7972` 走到 `_loop_handle_child_region_entry` 的**哪个分支**、
该分支把 `_x_ast` 追加进 `body_stmts` 了吗？若「return True 但没追加」，那才是这条语句真正
被吞的位置；若它压根没走到（被 `generated_blocks` 早退挡住），则要把 T12-05/06 的同一豁免
应用到 `:8868`/`:13884` 的认领循环上。探针形制已验证可用：把 `body_stmts` 长度与
`handled` 返回值在 co_name=='clock_worker' ∧ block.start_offset==7972 时打到 stderr，
跑完与封存产物逐字节比对自证惰性。

不要重复的动作：不要再加第三条「兄弟入口未渲染则不认领」的判据变体——那条已随 T12-06 装在
`_process_if_blocks` 的认领循环里且经 quotation/handlers 逐字节验证安全；现在的瓶颈是**循环体路径**。
