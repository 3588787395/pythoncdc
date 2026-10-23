# Task 9.6 — 门禁集成、双读数与审计

## 结论

- 已实现 `semantic_runner.py`，首次把 J 的 source、pyc、product、`semantic_diff` verdict 与 judge hash 写入同一 C1–C5 记录。
- 已实现 `gate_report.py` 与 `dual_readings.py`；门禁结果为 **BLOCKED**，不是 PASS。
- 本轮的 J 证据是**样本**：前 100 条中 51 条有可执行源/pyc，另 49 条 C1 缺失；不是全量 1556。
- 样本 51 条中 `45 EQUAL / 6 DIFFERENT`，6 条全部只报 R7；这说明判定空间并非全绿，不能写「J 门槛达标」。
- G5 的 6617/6617 等读数是**历史基线证据**，本轮没有重新跑 574 秒回归；报告显式标 `baseline_only=true`。
- 门禁阻断项：G1、G2a、G2b、G2c、G3、G4、G6；G5 是唯一 PASS，但也只是回归基线。

## 新增工具

```text
tools/completeness/semantic_runner.py
tools/completeness/gate_report.py
tools/completeness/gate_report_selftest.py
tools/completeness/dual_readings.py
```

运行：

```powershell
python -X utf8 tools\completeness\semantic_runner.py `
  --space .trae\specs\attack-completeness-claims\rounds\round9\judgment_space.json `
  --out .trae\specs\attack-completeness-claims\rounds\round9\semantic_j_sample.json `
  --report .trae\specs\attack-completeness-claims\rounds\round9\semantic_j_sample_summary.json `
  --limit 100 --timeout 15 --seconds 240

python -X utf8 tools\completeness\coverage_checker.py `
  --space .trae\specs\attack-completeness-claims\rounds\round9\judgment_space.json `
  --evidence .trae\specs\attack-completeness-claims\rounds\round9\semantic_j_sample.json `
  --judge tools\completeness\semantic_diff.py `
  --out .trae\specs\attack-completeness-claims\rounds\round9\COVERAGE_C1C5_SAMPLE.md `
  --json .trae\specs\attack-completeness-claims\rounds\round9\coverage_c1c5_sample.json `
  --allow-uncovered

python -X utf8 tools\completeness\gate_report.py
python -X utf8 tools\completeness\dual_readings.py `
  --gate .trae\specs\attack-completeness-claims\rounds\round9\gate_report.json `
  --out .trae\specs\attack-completeness-claims\rounds\round9\dual_readings.md
```

## J 样本读数

`semantic_j_sample_summary.json`：

| verdict | 数量 |
|---|---:|
| EQUAL | 45 |
| DIFFERENT | 6 |
| 有效记录 | 51 |
| C1 缺失跳过 | 49 |

6 个 DIFF：

| entry | dimensions | 说明 |
|---|---|---|
| `JS-IF-017` | R7 | 模块 docstring 形式差异（product 写 `__doc__ = ...`） |
| `JS-IF-021` | R7 | R7 差异 |
| `JS-IF-076` | R7×5 | 多处 metadata 差异 |
| `JS-IF-088` | R7 | R7 差异 |
| `JS-IF-090` | R7 | R7 差异 |
| `JS-IF-097` | R7 | R7 差异 |

这些不是用「等价」话术抹掉的失败；已如实进入 `semantic_failures`。是否属于既有 B 族、docstring 形式是否应改判、以及是否需要 product 修复，留给 Task 10 去重和裁决。

`coverage_c1c5_sample.json`：

- `J_total=1556`
- `covered_5tuple=51`
- `coverage_pct=3.28`
- `probe_only=1117`
- `uncovered=1505`（其中 388 条 C1 源缺失，其余为无完整 C3/C4/C5）
- `semantic_failures=6`
- `green=45`

## 门禁表

| gate | status | 依据 |
|---|---|---|
| G1 | FAIL | 51/1556 C1–C5；要求全覆盖 |
| G2a | FAIL | 样本 51 条已有 6 DIFF；未达 100 条且非零 DIFF |
| G2b | UNESTABLISHED | 没有 402 artifact 的 semantic_diff 证据 |
| G2c | UNESTABLISHED | 没有 46 个真实项目 pyc 的 semantic_diff 证据 |
| G3 | UNESTABLISHED | 没有全量 mutation report；只有 9/9 自测与 1/1 冒烟 |
| G4 | INCONCLUSIVE | 339 rules，0 proved，`no_rule_traces` |
| G5 | PASS | 历史基线 6617/6617、1568/1568、153/153、tests 基线、IV.2；本轮未重跑 |
| G6 | FAIL | 20/24 canary EQUAL；0 leak；local-bootstrap |

`overall=BLOCKED`，阻断项：G1、G2a、G2b、G2c、G3、G4、G6。

## 双读数

| 读数 | 值 |
|---|---|
| 形态基线（仅回归） | 6617/6617；small34 1568/1568；quotation 153/153；v8 128/0/0（100%） |
| 判定空间（C1–C5） | 51/1556 covered（3.28%）；6 DIFF；1505 uncovered（集成样本） |
| 规则 | 339 rules；0 proved；339 open |
| 金丝雀 | 20/24 EQUAL |

允许声明：**形态基线达成（仅回归）**。
禁止声明：**J 门槛达标**、**语料完备**、**规则完备**、**语义完备**。

## 审计

- `gate_report.py` 从 semantic 样本中确定性抽取 10%：6/51。
- 至少 1 个失败记录：是（抽中 DIFFERENT）。
- 6/6 的 C1/C2/C3 实文件 hash 与 C5 链一致。
- 审计只覆盖样本，不是全量 1556 的独立审计。

`gate_report_selftest.json` 12/12：覆盖 G1 完整/不完整、G2a 样本失败、G3 survived、G4 INCONCLUSIVE、G5 基线、G6 FAIL/缺失、整体 BLOCKED 和失败抽样。

## 边界与后续

- 没有伪造 G2b/G2c/G3 证据；没有把历史 G5 回归写成「本轮重跑」。
- 没有完成全量 J 的 C3/C4/C5 生产；Task 10 若要 G1，需要先跑全量并在 388 条 C1 缺失上明确挂账。
- `semantic_runner` 使用 `semantic_diff.py` 作为 judge；C5 的 judge hash 是 `semantic_diff.py` 的 sha256。
- 本轮没有修改 `core/cfg`；G5 的 `core_cfg_clean` 由 gate_report 现场检查。
- 下一步：Task 9.7 文档/提交；Task 10 逐项封闭与全量门禁。
