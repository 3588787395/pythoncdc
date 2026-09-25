# Round 70 · 批次 diag4（3 支 / 权重 8）

**本轮 mandate：至少一支 partial 修到官方 100%（全清）。** 你批内 `fileio_utils` gap 2、
`order_api` gap 2、`risk_calculation/__init__` gap 2 —— 三支都有现实的全清机会，`fileio`
只有 2 个 seq_len 缺陷（write 637→636、acquire 98→93），建议最先攻。

## 靶支与轮初基线（中心 2026-09-25 实测，landed = R69 HEAD 5647e97b）

| pyc | 官方 matched | 严格尺 | 严格缺陷数 |
|---|---|---|---|
| `IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` | **32/34**（gap 2） | **33/36** | 3 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | **33/35**（gap 2） | **34/37** | 3 |
| `IQCommon/util/fileio_utils.pyc` | **12/14**（gap 2） | **13/15** | 2 |

严格缺陷明细：

order_api：
- `base_order` [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=('order_obj','LOAD_FAST') decomp=('生成订单，订单号:{order_id}…（常量）
- `future_order` [seq_len] 101→93
- `option_order` [seq_len] 83→74

risk_calculation/__init__：
- `_on_publish_after_trading_end` [seq_len] 488→481
- `_on_set_positions` [seq_len] 297→298
- `_save_testds_to_csv` [seq_len] 75→72（R69 已从 68→72，嵌套 hunk 7→4，继续收口）

fileio_utils：
- `write` [seq_len] 637→636
- `acquire` [seq_len] 98→93

## 已知死胡同（别重复花预算）
- R69 回退 `cand_r69d4_orchain_legit`（order_api）：order_api 官方 Σ|Δ| 19→57、
  `future_order`/`option_order` 两支更差、合成 `r69d4_orchain` 2/6→2/6 不咬合。
  同向候选必须先过「Σ|Δ| 不升 + 两支合成咬合」才做 spec。

## 10 支合集口径（A/B 对照列）
- 官方：415/449 matched、gap 34、Σ|Δ| 195、Σhunk 147。
- 严格：436/488、缺陷 52。
- 45 项电池 landed 182/200、缺陷 18、worse=0；扩展电池（closeout69）318/356、缺陷 37。
- 金丝雀 sha：`4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`。
