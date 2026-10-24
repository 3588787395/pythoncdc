# VERIFICATION（round12 终态核验，rr-v5r08）

- 基本比较器：`scripts/pyc_verify.py` sha256 fe1902a90cebd4a1…（65a331ea 后零改动）；
  `pylingual/equivalence_check.py`、`tests/` 零改动（git diff clean）。
- 形态基线（本树实测）：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、
  fuzz 24/24 EQUAL、全量 pytest（--ignore=tests/nook）406 失败清单与冻结基线逐字节一致。
- 判定基线（本树实测）：见 GATE_REPORT_V5R06（overall BLOCKED）与 TASK5_THREE_LISTS。
- B142 定向：p_g1 3/3、p_g2 2/3、p_g3 2/3（冻结基线持平）；B142 族 4/5 项出口终结符挂账在案。
- 探针：probes_x01 7/7 + semantic EQUAL；probes_fz 7/7 + semantic EQUAL；023/015 min 2/2。
- 签名校验器：14 错误基线持平。
