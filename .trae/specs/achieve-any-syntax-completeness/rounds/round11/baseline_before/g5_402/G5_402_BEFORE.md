# 402 G5 基线 before 读数（Task 0.5）

命令（i=0..7；8 分片并行）：

```
python -X utf8 scripts\pyc_verify.py batch --index .trae\specs\region-reduction-v3-full-corpus-100pct-10rounds\baseline\shards\shard{i}.json --json <OUT>\g5_402\shard{i}_report.json
```

日期：2026-10-24。基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 `pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。

## 分片读数

| 分片 | 文件数 | success/failure/compile_error/error | 单元（含嵌套） | 单元率 | 耗时 |
|---|---:|---|---:|---:|---:|
| shard0 | 51 | 51/0/0/0 | 786/786 | 100.0% | 106.7s |
| shard1 | 51 | 51/0/0/0 | 469/469 | 100.0% | 76.1s |
| shard2 | 51 | 51/0/0/0 | 538/538 | 100.0% | 48.5s |
| shard3 | 51 | 51/0/0/0 | 887/887 | 100.0% | 74.7s |
| shard4 | 51 | 51/0/0/0 | 855/855 | 100.0% | 80.2s |
| shard5 | 51 | 51/0/0/0 | 999/999 | 100.0% | 86.1s |
| shard6 | 51 | 51/0/0/0 | 801/801 | 100.0% | 102.8s |
| shard7 | 45 | 45/0/0/0 | 1282/1282 | 100.0% | 113.4s |
| **合计** | **402** | **402/0/0/0** | **6617/6617** | **100.0%** | — |

对照历史口径：402 语料八分片历史读数 **6617/6617 全绿**；本次复跑 **6617/6617 全绿**，逐分片文件数 51×7+45=402 一致。结论：402 G5 基线 before 读数与历史读数**一致**。

注：单元数为 pyc_verify batch 报告的 `units_total`（含嵌套 code object），shard 索引内 `function_count`（仅顶层函数）之和 5746 为不同口径，勿混用。
