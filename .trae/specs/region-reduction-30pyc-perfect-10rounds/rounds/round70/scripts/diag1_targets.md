# Round 70 · 批次 diag1（1 支 / 权重 16）

**本轮 mandate：至少一支 partial 修到官方 100%（全清）。** 你批内最大杠杆是
`trade_live_broker`（官方 gap 10、严格缺陷 16）；先做 Step 0，再按官方 gap 从大到小逐支攻。

## 靶支与轮初基线（中心 2026-09-25 实测，landed = R69 HEAD 5647e97b）

| pyc | 官方 matched | 严格尺 | 严格缺陷函数 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | **109/119**（gap 10） | **107/123**（bad 16） | 见下 |

严格缺陷明细（kind / orig / decomp 条数或跳转信息）：

- `_process_cancel_order` [seq_len] 295→297
- `_process_order` [seq_len] 454→399
- `_process_tick_order` [target_diff] #27 JUMP 终点 orig=('len','LOAD_GLOBAL') decomp=('self','LOAD_FAST')
- `_sync_worker` [seq_len] 350→347
- `_trade_status_handle` [seq_len] 114→112
- `etf_basket_order` [seq_diff] #254 orig=('strategy_log','LOAD_GLOBAL') decomp=('entrust_price','LOAD_FAST')
- `etf_purchase_redemption` [seq_len] 379→369
- `get_ipo_stocks` [target_diff] #189 POP_JUMP_IF_TRUE 终点 orig=('str','LOAD_GLOBAL') decomp=(None,'FOR_ITER')
- `get_max_amount` [seq_len] 201→213
- `ipo_stocks_order` [seq_diff] #624 orig=('new_stock','LOAD_FAST') decomp=('<JUMP>','JUMP')
- `on_order_response` [seq_len] 449→448
- `on_order_response_list_handle` [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=('entrust_no','LOAD_FAST') decomp=(None,'FOR_ITER')
- `on_pre_before_trading_start` [target_diff] #4 POP_JUMP_IF_FALSE 终点 orig=('self','LOAD_FAST') decomp=('datetime','LOAD_GLOBAL')
- `on_trade_response` [seq_len] 396→395
- `on_trade_response_list_handle` [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=('entrust_no','LOAD_FAST') decomp=(None,'FOR_ITER')
- `rzrq_credit_order` [target_diff] #406 JUMP 终点 orig=('Order','LOAD_GLOBAL') decomp=('EntrustDirection','LOAD_GLOBAL')

R69 在本支的已知进展：`after_trading_cancel_order` 155/155 转绿（analyzer
`_check_elif_chain` 链尾合并豁免）。R69 已知未竟：`get_max_amount` 仍有约 10 缺口。

## 10 支合集口径（A/B 对照列）
- 官方：415/449 matched、gap 34、Σ|Δ| 195、Σhunk 147。
- 严格：436/488、缺陷 52。
- 45 项电池 landed 182/200、缺陷 18、worse=0；扩展电池（closeout69，含 round68/69 见证）318/356、缺陷 37。
- 金丝雀 sha：`4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`。
