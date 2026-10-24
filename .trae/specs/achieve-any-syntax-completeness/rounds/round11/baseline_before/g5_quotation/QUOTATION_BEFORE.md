# quotation before 读数（Task 0.5）

```
python -X utf8 scripts\pyc_verify.py single site-packages\fly\data\quotation.pyc
```

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

原始输出（末三行）：

```
[single] F:/Downloads/pythoncdc-main/site-packages/fly/data/quotation.pyc
[single] 浜х墿 F:/Downloads/pythoncdc-main/site-packages/fly/data/quotationOK.py
[single] status=success units=153/153 success_rate=100.00%
```

| 项 | 历史读数 | 本次复跑 |
|---|---:|---:|
| status | success | success |
| 单元 | 153/153 | 153/153 |
| 单元率 | 100% | 100% |

结论：与历史 153/153 **一致**。
