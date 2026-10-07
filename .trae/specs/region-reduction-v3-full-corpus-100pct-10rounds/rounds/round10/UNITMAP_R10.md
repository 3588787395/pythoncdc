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
