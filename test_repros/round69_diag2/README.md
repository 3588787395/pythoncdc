# round69_diag2

来源 `D:/Temp/opencode/r69gate/diag2`（Round 69 批次 B2，名下单矿 `fly/data/quote.pyc`）；采纳 spec：`cand_r69diag2_a.json`（region_ast_generator 1 edit，[R69-diag2-A while cond-chain prefix]：while 条件链前导段的完整非-Assign 语句段（段尾指令 ∈ STORE_*/POP_TOP）不再被 `type == 'Assign'` 判据误杀，改走与回边重检分段器逐字相同的 `_build_store_statement → _build_statement` 三级追加）。

消费者：`quote.pyc` 官方 **70/81 → 72/81**（`check_limit`、`initImagedata` 转绿，`get_real_from_zeromq` 703/678 → 703/700），Σ|Δ| **121 → 62**；严格 **74/89 缺陷 15 → 76/89 缺陷 13**，无新增 `target_diff`。判定臂：`landed` → `m69`。

| 见证 | landed → m69 |
|---|---|
| `r69diag2_whilepre.pyc` | 1/2 bad=1 → **2/2 bad=0** |
| `r69diag2_whilepre2.pyc` | 2/2 bad=0 → 2/2 bad=0（对照片，不变） |

对照留档：R68 撤回件 `cand_r68_else_join_cut`（同文件另一族，实测 matcher 715/715→713/466、quote 70/81→64/81）**本件与之不同族** —— 本件 matcher 17/17 不变、nested_diff 两侧逐字节相同、quote 只增不减；判定依据与读数留档归档 `rounds/round69/batches/b2_diag2`。

`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
