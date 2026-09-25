# Round 70 · 批次 diag5（2 支 / 权重 2）—— **全清第一候选批**

**本轮 mandate：至少一支 partial 修到官方 100%（全清）。** 你批两支官方 gap 都只有 **1**：
- `realtime_event_source` **11/12**（唯一严格缺陷 `clock_worker` seq_len 1276→1287，多发射 11 条）
- `api_base` **24/25**（唯一严格缺陷 `get_history_df` seq_diff #419 极性）

**优先攻 `realtime_event_source`**：单函数、纯条数差，修好即可能直接全清。
`api_base` 的极性缺陷与 klinedata `kline_datetime_list #151` 同签名（R69 判「过重」死胡同），
若无更轻的同层次判据就如实记 NONE，把时间花在 realtime。

## 靶支与轮初基线（中心 2026-09-25 实测，landed = R69 HEAD 5647e97b）

| pyc | 官方 matched | 严格尺 | 严格缺陷数 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | **11/12**（gap 1） | **11/12** | 1 |
| `IQData/api/api_base.pyc` | **24/25**（gap 1） | **26/27** | 1 |

严格缺陷明细：

- `realtime_event_source::clock_worker` [seq_len] orig=1276 decomp=**1287**（过冲 11 条）
- `api_base::get_history_df` [seq_diff] #419 orig=('<JUMP>','POP_JUMP_IF_TRUE') decomp=('<JUMP>','POP_JUMP_IF_FALSE')

## 已知死胡同（别重复花预算）
- R69 diag3 判 NONE：`get_history_df #419` 极性反需把 `inline_boolop_chains` 扩成可嵌套
  结构（6 读点），中心判「过重」。
- R67 教训：`jump_only` 盲区会出现「产物 UnboundLocalError 的假修」——任何候选必须
  `py_compile` 产物 + 官方/严格/合成三尺同测。

## 10 支合集口径（A/B 对照列）
- 官方：415/449 matched、gap 34、Σ|Δ| 195、Σhunk 147。
- 严格：436/488、缺陷 52。
- 45 项电池 landed 182/200、缺陷 18、worse=0；扩展电池（closeout69）318/356、缺陷 37。
- 金丝雀 sha：`4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`。
