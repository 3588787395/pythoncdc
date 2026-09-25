# Round 70 · 批次 diag2（1 支 / 权重 13）

**本轮 mandate：至少一支 partial 修到官方 100%（全清）。** 你批内唯一靶支 `fly/data/quote`
官方 gap 9、严格缺陷 13 —— 全清难度大，但 R69 已把该支 Σ|Δ| 从 121 压到 62，继续按族收口。

## 靶支与轮初基线（中心 2026-09-25 实测，landed = R69 HEAD 5647e97b）

| pyc | 官方 matched | 严格尺 | 严格缺陷函数 |
|---|---|---|---|
| `fly/data/quote.pyc` | **72/81**（gap 9） | **76/89**（bad 13） | 见下 |

严格缺陷明细：

- `build_current_period_df` [seq_len] 118→109
- `change_his_to_backward` [target_diff] #213 POP_JUMP_IF_TRUE 终点 orig=('data','LOAD_FAST') decomp=('None','POP_TOP')
- `change_his_to_forward` [target_diff] #241 POP_JUMP_IF_FALSE 终点 orig=('preindex','LOAD_FAST') decomp=(None,'FOR_ITER')
- `check_frequency` [seq_len] 123→124
- `check_industry_code` [seq_diff] #159 orig=('0','CONTAINS_OP') decomp=('1','CONTAINS_OP')
- `get_individual_data` [seq_len] 314→313
- `get_price` [seq_len] 230→232
- `get_real_from_zeromq` [seq_len] 703→700
- `load_bars_from_hundsun` [seq_len] 477→483
- `load_get_price` [seq_diff] #53 orig=('<JUMP>','POP_JUMP_IF_FALSE') decomp=('None','POP_TOP')
- `run_individual_transform` [seq_len] 364→321
- `run_tick_socket` [seq_len] 309→310
- `run_tick_transform` [target_diff] #56 POP_JUMP_IF_FALSE 终点 orig=('len','LOAD_GLOBAL') decomp=('self','LOAD_FAST')

R69 在本支的已知进展：`check_limit`、`initImagedata` 转绿（generator while 条件链前导段修复）、
`get_real_from_zeromq` 703/678→703/700。本支 `change_his_to_forward`/`get_trend` 属金丝雀
`quotation` 同名残余族（见 §已知死胡同）。

## 已知死胡同（别重复花预算）
- R69 diag3 判 NONE：guard 尾 or 子链致 and 链游走（`kline_datetime_list #151` 与
  `api_base::get_history_df #419` 同签名极性反）——修复需把 `inline_boolop_chains` 扩成可嵌套
  结构（6 读点），中心判「过重」。除非你有显著更轻的同层次判据，否则不要重开。
- R68/R69 多次实测：官方尺对 `quote` 的跳转容差与严格尺不一致，追求「严格全绿」可能反而
  动摇官方读数；**以官方 gap 与 ADR-1 双支判据为准**。

## 10 支合集口径（A/B 对照列）
- 官方：415/449 matched、gap 34、Σ|Δ| 195、Σhunk 147。
- 严格：436/488、缺陷 52。
- 45 项电池 landed 182/200、缺陷 18、worse=0；扩展电池（closeout69）318/356、缺陷 37。
- 金丝雀 sha：`4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`。
