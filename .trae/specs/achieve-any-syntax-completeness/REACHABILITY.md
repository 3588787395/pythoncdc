# 可达性表（REACHABILITY）

> 基线 commit：`e755d773`　|　表状态：`READY`（五行全部可达）　|　生成日期：2026-10-23
> 本表是 `achieve-any-syntax-completeness` 规范 Task 0.0–0.2 的**实现前产出并评审**文件。
> `READY` 的含义：五行每一格都给出了**有限输入来源、已存在的生成器/执行器、明确验收命令、明确阈值**，且命令与输入路径已于 2026-10-23 实测可达（见「可达性验证记录」节）。`READY` 不表示阈值读数当前已达成；阈值达成情况由 Task 1–7 逐门禁验收，任一格为空或为占位值即 `NOT READY`，不得进入实现。

## 术语对照：三个「五」

本规范同时出现三个「五」，它们指不同的东西，不得混用：

| 术语 | 指什么 | 内容 |
|---|---|---|
| **J 的五个维度** | 判定空间的坐标轴 | 形态、宿主、深度、变体、可调用性 |
| **J 记录的五个字段** | 每条 J 的最低存储字段 | `p_j`、`pyc`、`expected_label`、`input_model`、`excluded` |
| **产品完备的五个组成部分** | 验收支柱 | J 空间（五个维度）、语义差分、变异测试、规则覆盖、G5 回归 |

三者关系：

- **五个维度**回答「判定什么」：一条 J 是这五个维度上的一个点（例：`形态=try/finally`、`宿主=for`、`深度=2`、`变体=continue`、`可调用性=有函数入口调用`）。
- **五个字段**回答「怎么存」：`expected_label` 承载前四个维度（形态/宿主/深度/变体），`input_model.calls` 承载第五个维度（可调用性）。哈希（`p_j_sha256`/`pyc_sha256`）、行数（`p_j_lines`）、`entrypoint` 等是**审计辅助字段**，不参与「五字段」定义。
- **五个组成部分**回答「怎么验收」：每一支都必须给出有限输入、已有工具、明确命令和阈值（见下方主表）。
- 每条 J SHALL 至少有一个可调用入口（`input_model.calls` 非空）；module-only 只能算导入证据，不能算语义覆盖。

## 主表：产品完备的可达组成（五行 × 五列）

| 组成部分 | 有限输入来源 | 生成/执行方式 | 验收命令 | 阈值 |
|---|---|---|---|---|
| **J 空间（五个维度）** | CPython 3.11 语法产生式（J v2 全量 **1556** 条，`j_schema_version=v2`） | `tools/completeness/jspace_generator.py` 按形态/宿主/深度/变体/可调用性生成 `p_j / pyc / expected_label / input_model / excluded`；覆盖检查用 `tools/completeness/coverage_checker.py` | ① `python -X utf8 tools/completeness/jspace_generator.py --evidence-root .trae/specs/attain-true-completeness/rounds --out .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --md .trae/specs/attack-completeness-claims/rounds/round9/JUDGMENT_SPACE.md`<br>② 覆盖检查：`python -X utf8 tools/completeness/coverage_checker.py --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --evidence .trae/specs/attack-completeness-claims/rounds/round9/semantic_j_sample.json --judge scripts/pyc_verify.py --out .trae/specs/attack-completeness-claims/rounds/round9/COVERAGE.md --json .trae/specs/attack-completeness-claims/rounds/round9/coverage_c1c5.json` | **1556 条全量**；`source_missing = 0`、`pyc_missing = 0`、`calls_missing = 0` |
| **语义差分** | J 空间（五个维度，1556 条）+ 402 语料 + 46 真实 pyc | `tools/completeness/semantic_runner.py` + `tools/completeness/semantic_diff.py`（R1–R7：返回值/stdout/stderr/事件序/副作用/异常/元数据） | ① `python -X utf8 tools/completeness/semantic_runner.py --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --out .trae/specs/attack-completeness-claims/rounds/round9/semantic_j_sample.json`<br>② 单案：`python -X utf8 tools/completeness/semantic_diff.py --case <case.json> --out <result.json>` | `unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败 |
| **变异测试** | J 空间（五个维度，1556 条）+ 402 语料 | `tools/completeness/mutation_test.py`（AST 变异总体从原始源 AST 生成，非从用例生成；幸存者默认 MISSED） | `python -X utf8 tools/completeness/mutation_test.py --case <case.json> --source <subject.py> --out <mutations.json>` | `missed = 0` |
| **规则覆盖** | **339** 条规则 | `tools/completeness/rule_manifest.json` + witness/trace 映射（`tools/completeness/rule_manifest.py` 对账） | `python -X utf8 tools/completeness/rule_manifest.py --check --universe .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json --manifest tools/completeness/rule_manifest.json --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --traces <rule_traces.json> --json .trae/specs/attack-completeness-claims/rounds/round9/rule_coverage.json` | `open = 0` |
| **G5 回归** | 402 八分片（shard0–7）/ small34 / quotation / IV.2 | 既有回归脚本（`scripts/pyc_verify.py` batch/single + pytest + IV.2 自检） | ① `python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/shards/shard0.json`（同法跑 shard1–shard7）<br>② `python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/small34_index.json`<br>③ `python -X utf8 scripts/pyc_verify.py single site-packages/fly/data/quotation.pyc`<br>④ `python -X utf8 -m pytest -q tests/test_algorithm_correctness.py test_deep_nesting_pressure.py test_control_flow_completeness_matrix.py test_complete_syntax_coverage.py test_boundary_cases.py test_core_functional.py`<br>⑤ IV.2 自检见 `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round9/VERIFICATION.md` §三 | 全绿（402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线、IV.2） |

## 可达性验证记录（2026-10-23 实测）

以下为对本表五行可达性的实际验证证据（命令 + 读数），全部于基线 commit `e755d773` 工作树上执行：

### 1. J 空间行

- **J 总数 = 1556**：`python -X utf8 -c "import json;d=json.load(open(r'.trae\specs\attack-completeness-claims\rounds\round9\judgment_space.json',encoding='utf-8'));print(len(d['entries']))"` → `1556`。该 JSON 为 dict，J 条目在其 `entries` 键下；`version=v1`、`j_schema_version=v2`，与「J v2 全量 1556 条」一致。
- **`input_model.calls` 现状读数**：1556 条中 **1556 条 `calls` 为空列表、0 条缺 `calls` 键、0 条非空**（即 100% 空）。这是 Task 5.3 必须补齐的债务：阈值 `calls_missing = 0` 当前未达成，但输入有限、工具与命令明确，行可达。
- **生成器/检查器存在且可运行**：`tools/completeness/jspace_generator.py --help` → 退出 0（usage：`--evidence-root/--out/--md/--stats`）；`tools/completeness/coverage_checker.py --help` → 退出 0（usage：`--space/--evidence/--judge/--out/--json` 等）。
- **证据根存在**：`.trae/specs/attain-true-completeness/rounds` 目录存在（生成命令 `--evidence-root` 参数指向它）。

### 2. 语义差分行

- `tools/completeness/semantic_runner.py --help` → 退出 0（usage：`--space/--out/--report/--judge` 等）。
- `tools/completeness/semantic_diff.py --help` → 退出 0（usage：`--case/--cases/--out`；文档串确认 R1–R7 与 INCONCLUSIVE 语义）。
- 输入 J 空间存在且 1556 条（见上）；402 语料见第 5 节分片读数；46 真实 pyc 为规范声明的有限输入（round6 offcorpus 样例族）。

### 3. 变异测试行

- `tools/completeness/mutation_test.py --help` → 退出 0（usage：`--case/--source/--out/--equivalents/--max-mutants/--operators` 等；文档串确认「幸存者默认 MISSED、INCONCLUSIVE/ERROR 不计 killed」）。
- 输入（J 空间 + 402 语料）存在性分别见第 1、5 节。

### 4. 规则覆盖行

- **规则数 = 339**：`rule_universe.json` 为 dict，`total_rules` 字段 = `339`，`len(d['rules'])` = `339`（逐条含 `rule_id/anchor/file/line/patterns` 等键）。
- `tools/completeness/rule_manifest.py --help` → 退出 0（usage：`--universe/--manifest/--jspace/--traces/--json/--generate/--check`）。
- `tools/completeness/rule_manifest.json` 存在（规则命令 `--manifest` 参数指向它）。

### 5. G5 回归行

- **8 个 shard 索引全部存在，条目数 = 51/51/51/51/51/51/51/45，总计 402**：`shard0.json`–`shard7.json`（`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/shards/`）逐个 `json.load` 计数。
- `small34_index.json` 存在，条目数 = 34。
- `site-packages/fly/data/quotation.pyc` 存在。
- IV.2 引用文件存在：`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round9/VERIFICATION.md`。
- pytest 命令中 6 个测试文件全部存在：`tests/test_algorithm_correctness.py`、`tests/test_deep_nesting_pressure.py`、`tests/test_control_flow_completeness_matrix.py`、`tests/test_complete_syntax_coverage.py`、`tests/test_boundary_cases.py`、`tests/test_core_functional.py`。

### 工具 `--help` 汇总（六工具全部退出 0）

| 工具 | `--help` 结果 |
|---|---|
| `tools/completeness/jspace_generator.py` | OK（判定空间生成器） |
| `tools/completeness/semantic_runner.py` | OK（C1–C5 证据生产器） |
| `tools/completeness/semantic_diff.py` | OK（R1–R7 语义差分比较器） |
| `tools/completeness/mutation_test.py` | OK（AST 变异驱动） |
| `tools/completeness/rule_manifest.py` | OK（规则清单与 G4 对账） |
| `tools/completeness/coverage_checker.py` | OK（C1–C5 覆盖检查器） |

### 路径存在性汇总

| 路径 | 存在 |
|---|---|
| `.trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json`（1556 条） | 是 |
| `.trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json`（339 条） | 是 |
| `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/shards/shard0.json` … `shard7.json`（51/51/51/51/51/51/51/45） | 是 |
| `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/small34_index.json`（34 条） | 是 |
| `site-packages/fly/data/quotation.pyc` | 是 |
| `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round9/VERIFICATION.md`（IV.2 §三） | 是 |
| `tools/completeness/rule_manifest.json` | 是 |

## 冻结基线

| 项 | 值 |
|---|---|
| 基线 commit | `e755d773`（`rr-v4r10: add attack results and completeness recommendations`） |
| `scripts/pyc_verify.py` SHA256 | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` |
| 外部 `D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py` SHA256 | `9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6` |

**比较器冻结要求**：`scripts/pyc_verify.py` 及其装载的 `pylingual/equivalence_check.py::compare_pyc` 的字节、行为、容差和 verdict 语义全部保持不变；本规范期间只允许在其外层新增报告/汇总，不得改变判定。**任何 SHA 或行为变化即验收失败**（记「比较器污染」，不得用新读数宣称完备）。执行级语义差分只能以新增工具 `tools/completeness/semantic_diff.py` 作为附加判据，基本比较器仍按原样独立运行。只读校验工具：`tools/completeness/freeze_check.py`（Task 0.4）；before 读数落盘：`rounds/round11/baseline_before/FREEZE_BASELINE.md`（Task 0.3）。
