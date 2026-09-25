# Round 70 · 批次 diag3（3 支 / 权重 13）

**本轮 mandate：至少一支 partial 修到官方 100%（全清）。** 你批内 `trade_info_utils` 官方
gap 仅 1、`klinedata` gap 2 —— 全清优先级高于大支；`real_quote` 4 支全是 seq_len 纯位移外的
条数差，适合逐支收口。

## 靶支与轮初基线（中心 2026-09-25 实测，landed = R69 HEAD 5647e97b）

| pyc | 官方 matched | 严格尺 | 严格缺陷数 |
|---|---|---|---|
| `IQCommon/api/klinedata.pyc` | **43/45**（gap 2） | **58/63** | 5 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | **40/44**（gap 4） | **41/45** | 4 |
| `IQCommon/util/trade_info_utils.pyc` | **39/40**（gap 1） | **37/41** | 4 |

严格缺陷明细：

klinedata：
- `get_history_common` [target_diff] #41 POP_JUMP_IF_NONE 终点 orig=('is_dict','LOAD_FAST') decomp=('fields','LOAD_FAST')
- `get_kline_by_count_new` [target_diff] #161 POP_JUMP_IF_NONE 终点 orig=('0','LOAD_CONST') decomp=('symbols','LOAD_FAST')
- `get_multiminute_his_data` [seq_len] 481→482
- `get_price_common` [target_diff] #114 POP_JUMP_IF_NONE 终点 orig=('frequency','LOAD_FAST') decomp=('is_dict','LOAD_FAST')
- `kline_datetime_list` [seq_diff] #151 orig=('<JUMP>','POP_JUMP_IF_TRUE') decomp=('<JUMP>','POP_JUMP_IF_FALSE')

real_quote：
- `get_cache_l2_data_by_one` [seq_len] 321→322
- `get_real_minute_kline` [seq_len] 253→256
- `get_tick_direction` [seq_len] 259→260
- `one_prod_to_ndarray` [seq_len] 606→608

trade_info_utils：
- `get_trade_status` [target_diff] #70 FOR_ITER 终点 orig=('return_trade_info','LOAD_FAST') decomp=('count','LOAD_FAST')
- `get_trade_unit_info` [seq_len] 240→241
- `set_trade_status` [target_diff] #113 JUMP 终点 orig=('count','LOAD_FAST') decomp=('exchange_flag','LOAD_FAST')
- `trade_operation` [seq_len] 304→302

## 已知死胡同（别重复花预算）
- R69 diag3 判 NONE：`kline_datetime_list #151` 极性反与 `api_base::get_history_df #419`
  同签名，修复需把 `inline_boolop_chains` 扩成可嵌套结构（6 读点），中心判「过重」。
  若你没有显著更轻的同层次判据，**跳过该函数**，把预算花在其余 4 支。

## 10 支合集口径（A/B 对照列）
- 官方：415/449 matched、gap 34、Σ|Δ| 195、Σhunk 147。
- 严格：436/488、缺陷 52。
- 45 项电池 landed 182/200、缺陷 18、worse=0；扩展电池（closeout69）318/356、缺陷 37。
- 金丝雀 sha：`4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`。
