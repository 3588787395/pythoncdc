# round68_diag5

来源 `D:/Temp/opencode/r68gate/diag5`（Round 68 批次 B4）；采纳 spec：`cand_r68_wizapib.json`（analyzer 2 edit，[R68-diag5]×2）。
消费者 `wizard_quant_api` 52→53/53（全清）、`api_base::get_history_df` [1742,1740,14,1263] → [1742,1742,11,89]。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。

| 见证 | prev → landed |
|---|---|
| `r68b4_apib_inc1.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68b4_apib_inc2.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68b4_apib_inc3.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68b4_apib_inc4.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68b4_apib_inc5.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68b4_apib_inc6.pyc` | 1/2 bad=1 → 1/2 bad=1 |
| `r68b4_apib_inc7.pyc` | 1/2 bad=1 → 2/2 bad=0 |
| `r68d5_trymerge.pyc` | 1/2 bad=1 → 2/2 bad=0 |

完整诊断与被拒候选见归档 `rounds/round68/batches/`；`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
