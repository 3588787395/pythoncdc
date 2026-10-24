# GATE_REPORT 快照（rr-v5r08 = GATE_REPORT_V5R06 读数）

| 门 | 读数 | 判定 |
|---|---|---|
| G1/G2a | 395/1556 covered、189 DIFF | FAIL |
| G2b | 57 EQUAL / 3 DIFF / 342 环境不可执行 | FAIL |
| G2c | 5 EQUAL / 24 DIFF（19 仅 R7）/ 17 环境 | FAIL |
| G3 | 样本 32 killed / 602 missed（全量未跑） | FAIL |
| G4 | trace 187/339、152 never-hit、proved=0 | FAIL |
| G5 | 6617/6617 等实质绿（gate 旧字符串口径 FAIL） | FAIL* |
| G6 | 无独立 custody | ASSURANCE_BLOCKED |

overall：BLOCKED；product_complete = NOT PASS。完整 JSON/MD 见
`attack-completeness-claims/rounds/round9/gate_report_v5r06.json|GATE_REPORT_V5R06.md`。
