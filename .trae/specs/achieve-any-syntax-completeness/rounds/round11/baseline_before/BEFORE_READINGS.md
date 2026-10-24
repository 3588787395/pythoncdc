# BEFORE_READINGS — Task 0.5 before 读数总表

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

工作目录：`.trae/specs/achieve-any-syntax-completeness/rounds/round11/baseline_before/`（本文件所在目录，下称 OUT）。

| # | 读数 | 命令 | 结果 | 与历史对照 |
|---|---|---|---|---|
| 1 | J 样本（semantic_runner，round9 同参数） | 见 `OUT\j_sample\J_SAMPLE_BEFORE.md` | 51 有效：45 EQUAL / 6 DIFFERENT；49 c1_source_missing 跳过；DIFF=JS-IF-017/021/076/088/090/097 | round9 逐项一致 |
| 2 | 402 G5 八分片（pyc_verify batch ×8） | 见 `OUT\g5_402\G5_402_BEFORE.md` | 402/402 文件全 success；单元 6617/6617（100%） | 历史 6617/6617 一致 |
| 3 | small34 | 见 `OUT\g5_small34\SMALL34_BEFORE.md` | 34/34 文件；单元 1568/1568（100%） | 历史 1568/1568 一致 |
| 4 | quotation | 见 `OUT\g5_quotation\QUOTATION_BEFORE.md` | success；单元 153/153（100%） | 历史 153/153 一致 |
| 5 | 46 真实 pyc（offcorpus，pyc_verify single ×46） | 见 `OUT\real46\REAL46_BEFORE.md` | 4 success / 7 compile_error / 35 failure；单元 2765/3079（89.80%） | round6 L4 攻击读数逐项一致 |

## 说明

- 以上均为**基线 commit `e755d773`（HEAD 即基线）** 上的 before 读数，供本规范后续 Task 的 after 对照。
- 复跑脚本：`OUT\summarize_before.py`（402/small34 汇总）、`OUT\run_real46.py`（46 真实 pyc）。
- J 样本的 6 个 DIFFERENT 与 46 真实 pyc 的 42 个非绿样本即本规范 Task 2/3/4/5/6 要消化的既知债务面，不因基线全绿而豁免。
- 402/small34/quotation 全绿仅说明**既有回归基线**在当前树上可复现；"任何语法完备"由 `REACHABILITY.md` 五行决定，与本表相互独立。
