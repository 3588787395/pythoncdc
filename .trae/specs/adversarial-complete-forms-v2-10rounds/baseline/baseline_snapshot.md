# 基线快照（Task 0.1 落盘）

生成时间：2026-10-04
代码基点：本地工作树 = 旧规范 `harden-completed-forms-10rounds` Round 10 终态（提交链 72f46912→b53d449c→0caea12b→f831eeae 终审归档 + fc2aa1b1 网络故障记录；**唯 push 未竟**，待推送 f831eeae/fc2aa1b1 由本规范 push 时一并补推）
验证工具：`scripts/pyc_verify.py`（ruler = pylingual-equivalence_check，sha256 前缀 9c7567bd6776b36b，interpreter 3.11.7）
用途：本规范全部 10 轮 compare 的 before 基线（fresh 生成，非旧规范 round1 时代的过期报告）。

> 承接勘误：初稿误记基点为 b49b5b61（round9）；git log 核实旧 Round 10 已完成终审归档，本快照读数与 round10 VERIFICATION.md 终态（6554/6617、369/402）逐位一致即为佐证。规范三件套 II.6/III.5 承接口径已同步修正（v6：形式层 128/128 = 100%，新登记自 B77 续接）。

## 1. 全量语料（402 pyc，8 分片）

| 分片 | 文件数 | units_total | units_success | 文件 success | 文件 failure |
|------|--------|-------------|---------------|--------------|--------------|
| shard0 | 51 | 786 | 777 | 46 | 5 |
| shard1 | 51 | 469 | 462 | 48 | 3 |
| shard2 | 51 | 538 | 537 | 50 | 1 |
| shard3 | 51 | 887 | 883 | 48 | 3 |
| shard4 | 51 | 855 | 848 | 46 | 5 |
| shard5 | 51 | 999 | 993 | 46 | 5 |
| shard6 | 51 | 801 | 789 | 48 | 3 |
| shard7 | 45 | 1282 | 1265 | 37 | 8 |
| **合计** | **402** | **6617** | **6554** | **369** | **33** |

- 单元读数：**6554/6617 = 99.05%**（与 spec II.6 承接基线一致，无回退、无漂移）
- 文件读数：**369/402 success**（33 failure、0 compile_error、0 error）

## 2. 小测试集（34 pyc，failing_index.json）

- `small_test_report.json`：**1505/1568 单元 = 95.98%**，文件 1/34 success（33 failure）
- 与承接基线 1505/1568 一致。

## 3. 单验锚点

- `site-packages/fly/data/quotation.pyc`：**152/153（99.35%）**，唯一失败单元 `***<module>.change_his_to_forward: Different control flow`。与承接基线一致。

## 4. 一致性声明

三组 fresh 读数与 spec II.6「承接读数基线」逐项相等（6554/6617、369/402、1505/1568、152/153），
与旧规范 round10 VERIFICATION.md 终态亦逐位一致，证明当前工作树即旧规范 Round 10 终态、无未登记改动。后续每轮 compare 以本目录 8 份 shard 报告为 before，
REGRESSIONS=0 为硬门禁（checklist §2）。

## 5. 文件清单

- `shards/shard0.json … shard7.json`：分片索引（402 路径，`{"path": …}` 数组）
- `shards/shard0_report.json … shard7_report.json`：fresh 基线报告（本快照 §1 读数来源）
- `failing_index.json`：34 pyc 小测试集索引（子代理验证面）
- `small_test_report.json`：小测试集 fresh 基线报告
- `baseline_snapshot.md`：本文档
