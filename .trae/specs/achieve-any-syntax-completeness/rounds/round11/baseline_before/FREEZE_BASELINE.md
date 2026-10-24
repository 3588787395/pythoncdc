# 冻结基线记录（baseline_before）

> 规范：`achieve-any-syntax-completeness`（Task 0.3）　|　记录日期：2026-10-23　|　工作轮：`rounds/round11`
> 本文件落盘**实现开始前**的基本比较器冻结基线与 `tests/` 清单。本规范期间任何 SHA/行为变化即验收失败（「比较器污染」），不得用新读数宣称完备。

## 1. 基线 commit 与 HEAD

| 项 | 值 |
|---|---|
| 基线 commit | `e755d773`（`rr-v4r10: add attack results and completeness recommendations`） |
| 记录时 HEAD | `e755d7733d5ba074411e4acdf60ccc5aa72d0c9a`（记录时与基线 commit 一致，即规范于基线 commit 上启动） |

## 2. 基本比较器冻结（SHA256）

| 文件 | SHA256（冻结值 = 实测值） | 实测结果 |
|---|---|---|
| `scripts/pyc_verify.py` | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` | 一致 |
| 外部 `D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py` | `9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6` | 一致 |

- `git diff -- scripts/pyc_verify.py`：**为空**（无未提交改动）。
- 外部比较器 SHA 与规范 spec.md 登记值**一致**。
- 冻结要求：`scripts/pyc_verify.py` 及其装载的 `pylingual/equivalence_check.py::compare_pyc` 的字节、行为、容差和 verdict 语义全部不变；只允许在其外层新增报告/汇总，不得改变判定。

## 3. 只读校验工具运行记录（Task 0.4）

命令：`python -X utf8 tools/completeness/freeze_check.py`

结果：**ALL PASS（5/5 checks），退出码 0**。

| 检查项 | pass | 实际值 |
|---|---|---|
| `pyc_verify_sha256` | true | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` |
| `external_equivalence_check_sha256` | true | `9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6` |
| `git_diff_pyc_verify_empty` | true | （空） |
| `git_diff_tests_empty` | true | （空） |
| `head_commit_recorded` | true | `e755d7733d5ba074411e4acdf60ccc5aa72d0c9a` |

工具路径：`tools/completeness/freeze_check.py`（只读，无第三方依赖；支持 `--json <out.json>` / `--md <out.md>`）。

## 4. `tests/` 基线清单

- 清单文件：[`tests_manifest.json`](./tests_manifest.json)（与本文件同目录，UTF-8 JSON）。
- 记录方式：遍历 `tests/` 下**所有文件（含子目录）**，逐文件记录相对路径 + SHA256（大写十六进制）+ 字节数。
- **文件总数：8287 个**；总字节数 **20,827,956**。
- 按扩展名分布（前四类）：`.py` 4059、`.pyc` 3864（绝大多数为 `__pycache__` 编译缓存）、`.json` 196、`.md` 168。
- 清单字段：`manifest / spec / task / baseline_commit / generated / root / file_count / total_bytes / files[]`，`files[]` 每项含 `path / sha256 / bytes`。
- 约束：本规范期间 `tests/` 基线**零改动**；`git diff --name-only -- tests/` 必须为空，任何改动即违反强约束，回退该 Task 并重做。

## 5. 说明

- 本目录（`rounds/round11/baseline_before/`）只承载 before 读数；after 读数由后续任务在对应工作轮产物中落盘。
- Task 0.5 的重基线复跑（当前 J 样本、402 G5 基线、46 真实 pyc 基线）由并行代理执行，不在本文件范围内。
