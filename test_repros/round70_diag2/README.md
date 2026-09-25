# round70_diag2 — c2 回退件（诚实见证，未落地）

diag2 名下唯一候选 `cand_r70diag2_af`（analyzer T1「三元归并块承载后继 if」+ generator T3
`_try_wrap_fstring_pending_call` 后继语句通道，2 edits / 2 文件）被中心**拆臂证伪**：

- T1 单上（`batches/b0_diag2_rejected/split_arm_readings.jsonl.txt` 第一段）：
  `quote::get_price` 230/232 → 230/**251**（更差），且
  `risk_calculation/__init__` 33/35 → **32/35**（新增 `get_daily_summary` 622/647 过冲）。
- T3 单上（同文件第二段）：quote / risk_calculation 双支读数与 landed 逐项相同（惰性）。
- T1+T3：quote 72 → 73/81（get_price 转绿）但 risk_calculation 回归仍在。

按 ADR-1（任何回归即拒）**整件回退**，quote 本轮维持 72/81。
无合成见证产出（判据未钉死不写见证）；spec 全文在 `rounds/round70/specs/cand_r70diag2_af_{0,1}.json`。
