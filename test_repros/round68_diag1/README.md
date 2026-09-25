# round68_diag1

来源 `D:/Temp/opencode/r68gate/diag1`（Round 68 批次 B1）；采纳 spec：`cand_r68_b1.json`（region_analyzer 3 edit，[R68-B]/[R68-C·循环豁免收紧]/[R68-E·merge 收集的剪枝守卫]）。
消费者 `matcher::match` 官方 16/17 → 17/17（全清）。判定臂：`prev`（R67 HEAD 字节）→ `landed`（R68 落地字节），本批 **REGRESSION=0**。

| 见证 | prev → landed |
|---|---|
| `e1.pyc` | 3/4 bad=1 → 3/4 bad=1 |
| `m2_r68.pyc` | 16/17 bad=1 → 17/17 bad=0 |
| `m_r68.pyc` | 17/18 bad=1 → 17/18 bad=1 |
| `s_r68.pyc` | 8/11 bad=3 → 8/11 bad=3 |
| `xp_atco.pyc` | 6/7 bad=1 → 6/7 bad=1 |
| `xp_atco2.pyc` | 6/8 bad=1 → 6/8 bad=1 |

完整诊断与被拒候选见归档 `rounds/round68/batches/`；`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
