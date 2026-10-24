# J 样本 before 读数（Task 0.5）

复跑命令（与 round9 `GATE_INTEGRATION.md` 完全同参数）：

```
python -X utf8 tools\completeness\semantic_runner.py --space .trae\specs\attack-completeness-claims\rounds\round9\judgment_space.json --out <OUT>\j_sample\semantic_j_sample_before.json --report <OUT>\j_sample\semantic_j_sample_before_summary.json --product-dir <OUT>\j_sample\semantic_products --limit 100 --timeout 15 --seconds 240
```

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

## 读数对照

| 项 | round9 历史 | 本次复跑 |
|---|---:|---:|
| 有效记录 | 51 | 51 |
| EQUAL | 45 | 45 |
| DIFFERENT | 6 | 6 |
| c1_source_missing 跳过 | 49 | 49 |
| stopped | skipped | skipped |

DIFFERENT 条目（与 round9 完全一致）：`JS-IF-017`, `JS-IF-021`, `JS-IF-076`, `JS-IF-088`, `JS-IF-090`, `JS-IF-097`。

结论：J 样本 before 读数与 round9 历史读数**逐项一致**，基线可复现。
