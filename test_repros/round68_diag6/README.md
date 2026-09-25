# round68_diag6

来源 `D:/Temp/opencode/r68gate/diag6`（Round 68 批次 B5）；采纳 spec：`cand_r68b5_initc.json`（generator 4 edit，[R68-diag6/b5 init-if] / [R68-diag6]×2 / [R68-diag6/b5]）。
消费者 `flyAccount` 21→23/23（全清）。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。

| 见证 | prev → landed |
|---|---|
| `r68d6_handler_return.pyc` | 4/4 bad=0 → 4/4 bad=0 |
| `r68d6_handler_return2.pyc` | 1/3 bad=2 → 3/3 bad=0 |
| `r68d6_tuple_ternary.pyc` | 3/4 bad=1 → 4/4 bad=0 |
| `r68d6_tuple_ternary2.pyc` | 1/3 bad=2 → 3/3 bad=0 |

完整诊断与被拒候选见归档 `rounds/round68/batches/`；`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
