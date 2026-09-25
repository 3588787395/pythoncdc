# round68_diag4

来源 `D:/Temp/opencode/r68gate/diag4`（Round 68 批次 B3）；采纳 spec：`cand_r68b3_combo.json`（generator 4 edit，[R68-b3 修复]×2 / [R68-D4-ORCHAIN-TAIL] / [R68-diag3 C3]）。
消费者 `trade_info_utils` 38→39/40、`logger` 29→30/30（全清）。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。

| 见证 | prev → landed |
|---|---|
| `r68b3_headif.pyc` | 4/7 bad=3 → 4/7 bad=3 |
| `r68d4_orchain.pyc` | 3/3 bad=0 → 3/3 bad=0 |
| `r68d4_s2.pyc` | 7/7 bad=0 → 7/7 bad=0 |
| `r68d4_s3.pyc` | 3/5 bad=2 → 5/5 bad=0 |

完整诊断与被拒候选见归档 `rounds/round68/batches/`；`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
