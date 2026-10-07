# Round 10 单元图（修好仪器后的权威分派表）

仪器：`D:/Temp/r9main/unitmap.py` → `D:/Temp/r9main/unitmap_r9.json` / `unitmap.txt`。
基线＝`rounds/round9/after`（封表读数 6577/6617、386/402、40 失败单元／16 文件），
产物读盘上现字节（已回滚到封表态后重生成）。

## 〇、本轮修掉的两个仪器缺陷（它们此前各自生产过一次假结论）

1. **嵌套 code object 按 `repr()` 比较**（含内存地址与文件名）⇒ 造出假差。
   现归一为 `<co 名/argcount/varnames数>`。
2. **跳转目标落在被剥离的行锚 `NOP` 上时无可比标签**⇒ 该差被抹平成「看不见」。
   现显式标 `ANCHOR`，于是「跳进锚点」与「跳进锚点后第一条实指令」重新成为**可比 difference**。

⇒ 旧结论两处被推翻：`load_daily.<module>` 不是「20 处说不清的差」，而是 **1 处纯落点差**；
`trade_live_broker._process_tick_order` 不是「仪器盲区」，而是 **1 处纯落点差（ANCHOR 型）**。

## 一、40 单元的权威分档（首中即止，谓词见仪器 docstring）

| 类 | 数 | 单元（文件名简写） | 归属 |
|---|---|---|---|
| `TARGET_ONLY`（**全部差都是同 opcode 仅目标不同，零内容差**） | **8** | `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`trade_live_broker.rzrq_credit_order`、`trade_live_broker._process_tick_order` | **#14（最纯的一档）** |
| `LOSS`（删多于插，**17 条逐一列全**） | **17** | `matcher.DefaultMatcher.match`(del25/ins15，**在飞 #13 P0**)、`__init__`(risk)`_on_publish_after_trading_end`、`__init__`(risk)`_save_testds_to_csv`、`quote.build_current_period_df`、`quote.get_real_from_zeromq`(del36/ins34)、`quote.run_individual_transform`(del84)、`realtime_event_source.clock_worker`(del180)、`handlers._target`(del17/ins15＝净 2，**属 #15**)、`trade_live_broker._process_cancel_order`(del300)、`._process_order`(del471)、`._sync_worker`(del192/ins189)、`._trade_status_handle`(del18)、`.etf_purchase_redemption`、`.ipo_stocks_order`(tgt35)、`order_api.future_order`(del30)、`order_api.option_order`(del42)、`trade_info_utils.query_strategy_id`(**属 #15**) | #13 主体；其中 `_target`/`query_strategy_id` 判据面归 **#15** |
| `EXTRA`（插多于删） | **7** | `quote.check_frequency`、`quote.get_individual_data`、`quote.run_tick_socket`、`real_quote.get_tick_direction`、`real_quote.get_real_minute_kline`、`wizard_quant_api.filter_desicion`、`klinedata.get_multiminute_his_data` | #13/#14（多为「别处 1 条摊成 9 条」的挪位形） |
| `MIXED`（有内容增删但净差为 0） | **5** | `trade_live_broker.etf_basket_order`(tgt32)、`api_base.get_history_df`(tgt14)、`klinedata.get_kline_by_count_new`、`klinedata.kline_datetime_list`(tgt25)、`trade_info_utils.query_trade_strategy_info`(**属 #15**) | `etf_basket_order`/`get_kline_by_count_new` 主体是目标差＝**#14**；`kline_datetime_list`/`get_history_df` 是 5→1 压形＝**#13** |
| `TRANSPOSED`（两条跳转目标**互相换位**） | 1 | `trade_info_utils.kill_trade_process` | #14 |
| `COPY_AMBIG`（同路径副本不唯一，**拒判**） | 2 | `wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2（orig 3 副本 / prod 3 副本） | 须人工按出现次序定标后才可开票 |
| `COPY_AMBIG`（同路径副本不唯一，**拒判**） | 2 | `wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2（orig 3 副本 / prod 3 副本） | 须人工按出现次序定标后才可开票 |

合计 8+1+17+7+5+2 = **40** ✓ 与封表失败单元数相符。

## 二、排产含义（按「一票能翻正几个文件」重排，不是按桶大小）

| 优先 | 票 | 本档能给的文件翻正 | 依据 |
|---|---|---|---|
| **1** | **#14（`TARGET_ONLY` 8 条）** | **4 个整文件**：`bar` 84/85、`strategy_universe` 10/11、`load_daily` 26/27、`strategy` 26/27（`_history_bars`/`_on_clear_de_listed`/`<module>`/`tick_worker_thread` 各自是所在文件的**唯一**失败单元） | 零内容差 ⇒ 一条落点判据即可，无共要件、无省略纠缠 |
| 2 | #13 P0（**在飞**） | `matcher` 16/17 → 17/17 | 单条被吞语句 |
| 3 | #15 | `handlers` 29/30 → 30/30；并 `trade_info_utils` 的 `query_strategy_id`/`query_trade_strategy_info` | 共享隐式尾声 epilogue 的身份（三单元一判据） |
| 4 | #13 次刀 | `order_api` 35/37（`option_order`+`future_order`）、`__init__`(risk) 41/43、`real_quote` 43/45 | 各自 del/ins 同形，且无 #16 共要件 |
| 5 | #13＋**#16 共要件** | `trade_live_broker` 118/128 的 `_process_order`/`_process_cancel_order`/`_trade_status_handle` | del 471/300/18，须先应用 `RAVED_R10_B126.patch`（见 `ADJUDICATION_R10_B126_REVERTED.md` §四） |
| 6 | 定标后另开票 | `wizard_quant_api` 55/58 | 两条 genexpr 副本不唯一，未定标前**禁止**开票 |

`quote` 86/92 需 6 条齐闭合，且 `run_individual_transform`(del84)/`clock_worker`(del180) 都是大省略——
按上表第 4/5 类的判据面拆刀，不设「一票吃下整文件」的预期。

## 三、纪律复用

- 本表是**逐单元**名单的唯一出处：任何票的「射程/成绩」按名单计，禁止用桶数或文件数推算。
- 每次落地后**必须重跑 `unitmap.py`** 再派下一票（成员关系与落点一改，本表就过期；
  Round 10 已两次因沿用旧名单而白跑）。
- 类定义里被丢掉的每个字段都是将来的假轴：本轮丢 `argrepr` 中的嵌套对象身份 ⇒ 假差；
  丢锚点 `NOP` ⇒ 假盲区。新增分类前先问「我这一版又隐藏了什么字段」。

## 四、`COPY_AMBIG` 两条已定标（2026-10-08，主代理自有复跑 ⇒ 解除「未定标禁止开票」）

配对方法：按 **`co_consts` 出现次序**枚举 `get_DMI/calculate_di/<genexpr>` 的三个副本，
两侧副本数相等（3/3），且**第 0 对逐指令全等**（`hunks=0, ratio=1.000`）——
这一条等式就是「按出现次序配对」正确性的证据：若次序错配，第 0 对不可能零差。
行号单调亦吻合（orig 385/388/390 ↔ prod 262/263/264）。

定标后两条失败副本的实测差**同一个形状**：

| 对 | 长度 | 内容差 | 被吞的 14 条（orig[7:21]） |
|---|---|---|---|
| pair[1]（`high`） | 64 → 50 | **1 处 delete＝14 条** | `LOAD_DEREF high / LOAD_FAST i / UNARY_NEGATIVE / BINARY_SUBSCR / LOAD_DEREF high / LOAD_FAST i / LOAD_CONST 1 / BINARY_OP + / …` |
| pair[2]（`low`） | 64 → 50 | **1 处 delete＝14 条** | 同形，把 `high` 换成 `low` |
| 其余 3 处 hunk | — | **全是偏移随 14 条而移**（`FOR_ITER 62→48`、`POP_JUMP_FORWARD_IF_FALSE 57→43`） | 不是独立缺陷 |

⇒ 机制读法：生成器表达式元素里的**负眼下标 + `+1` 偏移操作数**这一整串操作数链被丢，
`wizard_quant_api.pyc` 现 55/58：这两条同判据面（一判据记 2 单元），第三条 `filter_desicion` 属 `EXTRA` 档另计。
本案与 #13 的 `etf_purchase_redemption`「属性链截断」同族（操作数链被截），
但它在 `<genexpr>` 内部 ⇒ **不得并案**，须各自以逐单元名单证明；
两处的共同宿主若被找到，须是一条不问「是否处在生成器内」的判据（原则 3：嵌套即抽象节点，
宿主对内部结构无感才算封闭）。

## 五、再定标两条（同轮复跑，逐 hunk）

**(a) `order_api.pyc`（35/37）的 `option_order` / `future_order` 共享同一对形状**——
两单元各只有 2 个大 hunk，且**互为镜像**：

| hunk | `option_order` | `future_order` | 被吞内容（实测指令串读回的语句） |
|---|---|---|---|
| 9 → 1 | `orig[38:47]` | `orig[71:80]` | `if <cond>: strategy_log.info('生成订单，订单号：{order_id}，合约代码：{symbol}，方向：{side}{oper}，数量：{share}手…'.format(order_.order_id, …))` —— **条件体里的一整条日志调用**，产物只留下那条 `POP_JUMP_FORWARD_IF_TRUE` |
| delete 31 / 19 | `orig[59:90]` | `orig[92:111]` | `order_.futures_direction.value.upper() == 'OPEN' and '开仓' or '平仓'` —— **属性链 + 方法调用 + 比较 + and/or 三元**的整串操作数（它原是上面那条格式串的实参） |

⇒ 一条判据面（长操作数链在**条件发射/汇合处**被截）记 2 单元；`real_quote` 不在本案（见 b）。
与 #21（`<genexpr>` 内的下标操作数链）同族不同层，仍禁并案：判据若须问「是不是在生成器里」即不封闭。

**(b) `real_quote.pyc`（43/45）两条被撤销「省略」归类**：
`get_tick_direction` 12 个 hunk、`get_real_minute_kline` 3 个 hunk，**零个大 hunk**（`big=0`）——
即没有任何多指令块被吞或被摊，两单元全部差在小粒度（≤4 指令的 replace/insert）。
`unitmap` 把它们记进 `EXTRA` 是按**净条数**（ins 12/del 11、ins 4/del 2）分类的结果，
不是省略证据。⇒ 这两条改归 **#14 的细粒度落点/排位面**，
派 #13 系票时**不得**把它们写进名单（先前我的 `FIX_OMISSION_R10_BRIEF.md` 未列它们，无须订正；
此处只钉住「EXTRA ≠ 省略」这条分类学事实，防下一次按桶名派票）。

## 六、类的**定义**改正：桶名不再等于工单（净条数与 hunk 大小都只是代理量）

§一/§五 暴露出同一个毛病两次：`LOSS`/`EXTRA` 是按**净条数**分的，于是
**纯搬位**（块从 A 处挪到 B 处）也被记成省略或多出。故 `unitmap.py` 的分类键改为
「**是否存在 ≥4 指令的多指令 hunk**」，净条数降为子标签：

| 新类 | 数 | 定义 | 工单含义 |
|---|---|---|---|
| `FINE_LANDING` | **20** | 无任何 ≥4 指令 hunk | 落点/排位面（#14 与其邻面）；**注意：仍可能含 ≤3 指令的小内容差** |
| `FINE_TRANSPOSED` | 1 | 同上且两条位移互取对方落点 | `kill_trade_process` |
| `CONTENT_OMISSION` | **11** | 多指令 hunk 删多于插 | #13/#21/#22 池 |
| `CONTENT_SPREAD` | 2 | 多指令 hunk 插多于删（摊开/搬位） | `kline_datetime_list`、`get_history_df` 一类 |
| `CONTENT_MIXED` | 4 | 多指令 hunk 收支相抵 | 须逐单元读机制 |
| `COPY_AMBIG` | 2 | 同路径副本不唯一 | 已定标（§四），按 `#21` 开票 |

**关键自我限制（写下来防再犯）**：`FINE_LANDING` **不等于**「无内容差」。
本档 §一 曾把 `handlers._target` 判成「看不见」、§五 曾把 `real_quote` 两条判成「省略」，
两次都是把代理量当机制。现给 `FINE_LANDING` 内部按 `net = del − ins` 列出**带小内容差**的单元，
供工单认领时复核，而非由类名推定：

| 单元 | net | 实测小内容差 | 认领票 |
|---|---|---|---|
| `handlers.TWHThreadController._target` | **+2** | 一对 `LOAD_CONST None/RETURN_VALUE` 未发（`orig[75:77]`） | **#15** |
| `trade_info_utils.query_strategy_id` | **+1** | 一处 `JUMP_FORWARD → 共用尾` 被写成内联 `LOAD_CONST None; RETURN_VALUE`，且另一处共用尾 2 条未发 | **#15** |
| `trade_info_utils.query_trade_strategy_info` | **0** | 两处内联（各 +1）与一处共用尾缺失（−2）相抵 ⇒ **净 0 不等于无缺陷** | **#15** |
| `wizard_quant_api.filter_desicion` | −2 | ≤3 指令的小摊开 | #14 邻面，派单前逐读 |
| `klinedata.get_multiminute_his_data` | −1 | 同上 | 同上 |
| `quote.check_frequency` / `quote.get_individual_data` | −1 / −1 | 同上 | 同上 |
| `real_quote.get_real_minute_kline` | −2 | 同上 | 同上 |
| `trade_live_broker.ipo_stocks_order` | +1 | 35 处目标差 + 1 条净少 | #14（D 档禁按 35 记账） |

其余 11 条 `FINE_LANDING`（`load_daily.<module>`、`bar._history_bars`、
`strategy_universe._on_clear_de_listed`、`strategy.tick_worker_thread`、
`get_trade_status`、`get_ipo_stocks`、`rzrq_credit_order`、`_process_tick_order`、
`get_kline_by_count_new` 等）`net=0` 且只由同 opcode 目标/锚点位移构成 ⇒ **#14 的纯落点名单**。

⇒ **本表是工作清单，不是分派表**：票面归属一律由 §二/§四/§五 的**具名机制**决定；
类名只用于排序与覆盖检查。（`matcher.DefaultMatcher.match` 一行在 #13-P0 工程师重生成产物期间可能瞬时失真，
本档结论不依赖它——该单元已由 §一 具名为「一条被吞的切片成员测试」。）

## 七、40 单元的**机制具名覆盖表**（本档的终点：把工作清单转成可派工单）

状态图例：**具名**＝已有可读回的语句/边事实；**半具名**＝知形状未定位宿主；**未具名**＝只有 hunk 计数。

| 票 | 单元（文件） | 具名机制 | 状态 |
|---|---|---|---|
| **#13-P0（在飞）** | `matcher.match` | 条件体内整条 `order.asset.symbol[None:3] in ('688','689')` 测试被吞（`big=10/0`，该文件唯一失败单元） | 具名 |
| **#22** | `order_api.option_order` / `future_order` | 镜像两形：条件体 `strategy_log.info('生成订单…'.format(…))` 被吞（9→1）＋ `…futures_direction.value.upper()=='OPEN' and '开仓' or '平仓'` 操作数链被吞（delete 31/19） | 具名 |
| **#21** | `wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2 | 生成器元素里负眼下标 + `+1` 偏移的操作数链被吞（各 `delete 14`，`high`/`low` 对称实例） | 具名 |
| **#15** | `handlers.TWHThreadController._target`、`trade_info_utils.query_strategy_id`、`query_trade_strategy_info` | 共享隐式尾声 epilogue 未被认成单一落点：产物逐路内联 `LOAD_CONST None/RETURN_VALUE`，共用尾反不发 | 具名 |
| **#16 共要件 ＋ #13** | `trade_live_broker._process_order`(big 469/3)、`_process_cancel_order`(298/4)、`_trade_status_handle`(9/5) | 结构改判（`while True:` + 体内 `if`）已由 `RAVED_R10_B126.patch` 解决；余下的大省略**未定位宿主** | **半具名** |
| #13 | `trade_live_broker.etf_purchase_redemption`(11/1) | 属性链截断 | 半具名 |
| #13 | `realtime_event_source.clock_worker`(144/27) | 一形三态：`if persist_flag is not False:` 110 条体被跳 ＋ 17 条块搬到循环后 ＋ 3 处目标差 | 具名 |
| #13 | `quote.run_individual_transform`(71/18) | 循环体半丢：`socket.recv()` → `message` → 空数据告警分支 → `list(...)[0]` 一串被压成 2 条（三处独立 hunk 同形） | 具名 |
| #13 | `quote.build_current_period_df`(12/2) | 函数尾被吞：`tempdict['is_open'] = …` ＋ `pandas.DataFrame(tempdict, index=…)` 构造整串消失，产物只剩 `POP_TOP; LOAD_CONST None` | 具名 |
| #13 | `plugin_system_risk_calculation._save_testds_to_csv`(14/5) | 只有计数（曾按 §二B 记为「`while…else` 的 else 体是 `return None`」，现测得 14 条真删）⇒ 需逐读 | **未具名** |
| #13/#14 | `klinedata.kline_datetime_list`、`api_base.get_history_df` | 5→1 压形（`time_count -= 1` 与其后循环测试算术）＋ 别处 1→9 摊开 | 具名 |
| #14 邻面 | `__init__._on_publish_after_trading_end`(2/2) | 函数内 `import`（`IMPORT_NAME`+`IMPORT_FROM` 成对消失）＋小摊开 | 具名 |
| #14（纯落点） | `bar._history_bars`、`strategy_universe._on_clear_de_listed`、`load_daily.<module>`、`strategy.tick_worker_thread`(含 2 处 ANCHOR)、`trade_info_utils.get_trade_status`、`trade_live_broker.get_ipo_stocks`、`rzrq_credit_order`、`_process_tick_order`(ANCHOR)、`ipo_stocks_order`、`kill_trade_process`(换位) | 汇合块/锚点归属；**方向不一**（有早有晚），单向规则必错 | 具名 |
| 未具名 | `wizard_quant_api.filter_desicion`(−2)、`klinedata.get_multiminute_his_data`(−1)、`klinedata.get_kline_by_count_new`(0)、`quote.check_frequency`(−1)、`quote.get_individual_data`(−1)、`quote.run_tick_socket`(27/28 搬位)、`trade_live_broker._sync_worker`(178/180 链式比较腿＋搬位)、`trade_live_broker.etf_basket_order`(13/13，落点副本不可分) | 只有 hunk 计数或已知「搬位而非省略」 | **未具名/待逐读** |

计数核对：具名 **24**、半具名 **5**、未具名 **11**，合计 **40** ✓。

**下一步取证次序（按「离翻正几个单元」排，不按桶大小）**：
1. `realtime_event_source`(12/13) 与 `plugin_system_risk_calculation`(41/43)、`quote`(86/92)、
   `klinedata`(61/64)、`trade_info_utils`(37/41) 中，**只差 1–2 单元的文件优先**：
   `realtime_event_source`、`matcher`(在飞)、`api_base`、`bar`、`strategy`、`strategy_universe`、`load_daily`、`handlers`；
2. 未具名的 8 条小差单元（`check_frequency`、`get_individual_data`、`get_multiminute_his_data`、
   `get_kline_by_count_new`、`filter_desicion`、`run_tick_socket`、`etf_basket_order`、`_sync_worker`）
   逐条读 hunk 语义后再定票面——**不得先给它们派票再找机制**；
3. 每票落地后重跑 `unitmap.py`，本表随之改版（本表已是第二次改版：分类键改正一次、real_quote 与 `_target` 各撤销一次）。
