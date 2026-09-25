# round68_diag3

来源 `D:/Temp/opencode/r68gate/diag3`（Round 68 批次 B2）；采纳 spec：`cand_r68b2_andchain.json`（analyzer 1 edit，[R68-b2 and-chain]）+ `cand_r68b2_final_gen.json`（generator 3 edit，[R68-b2 cell-swap]×2）。
消费者 `klinedata` 42→43/45、`scheduler` 44→45/45（全清）。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。

| 见证 | prev → landed |
|---|---|
| `r68_big_sinkreturn.pyc` | 1/3 bad=2 → 1/3 bad=2 |
| `r68_sink_continue.pyc` | 1/2 bad=1 → 2/2 bad=0 |
| `r68_sink_return.pyc` | 2/2 bad=0 → 2/2 bad=0 |
| `r68_sink_tailreturn.pyc` | 4/4 bad=0 → 4/4 bad=0 |
| `r68b2_cell_tuple.pyc` | 2/3 bad=1 → 3/3 bad=0 |
| `r68b2_cell_tuple_body.pyc` | 2/3 bad=1 → 3/3 bad=0 |

完整诊断与被拒候选见归档 `rounds/round68/batches/`；`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
