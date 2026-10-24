# small34 before 读数（Task 0.5）

```
python -X utf8 scripts\pyc_verify.py batch --index .trae\specs\region-reduction-v3-full-corpus-100pct-10rounds\baseline\small34_index.json --json <OUT>\g5_small34\small34_report.json
```

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

| 项 | 历史读数 | 本次复跑 |
|---|---:|---:|
| 文件 | 34 | 34 |
| status success/failure | 34/0 | 34/0 |
| 单元 | 1568/1568 | 1568/1568 |
| 单元率 | 100% | 100.0% |
| 耗时 | — | 157.5s |

结论：与历史 1568/1568 **一致**。
