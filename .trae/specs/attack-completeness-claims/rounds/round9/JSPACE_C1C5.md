# Task 9.3 判定空间与 C1–C5 覆盖

- 生成器：`tools/completeness/jspace_generator.py` v2.0.0，schema `v2`
- 检查器：`tools/completeness/coverage_checker.py` v2.0.0
- 自测：`tools/completeness/coverage_checker_selftest.py`，13/13 通过
- 证据：`rounds/round9/JUDGMENT_SPACE.md`、`judgment_space.json`、`COVERAGE_C1C5.md`、`coverage_c1c5.json`、`coverage_checker_selftest.json`

## 1. 旧口径的问题

旧 `coverage_checker.py` 的唯一判据是：条目的 `required_evidence[].pyc` 命中 `rec1_probes_*.json` 索引，即 `covered`。

这只能证明「探针文件被登记过」，不能证明：

- 源文件存在且与登记内容一致；
- pyc 可被当前解释器加载；
- 有反编译产物；
- 有执行级判定；
- 哈希链把源、pyc、产物、判定、判据版本绑在同一条记录。

因此旧读数 `976/1556 = 62.72%` 是 **probe-only**，不是五元组覆盖。B170 的修复从这里开始。

## 2. J schema v2

生成器现在为每条条目写入：

```json
{
  "id": "JS-IF-001",
  "j_schema_version": "v2",
  "expected_label": {"form": "If", "variant": "if-no-else",
                     "host": "module-level", "depth": "d1 单层"},
  "p_j": "test_repros/round2/m02_top_ifmain.py",
  "p_j_sha256": "...",
  "p_j_lines": 35,
  "pyc": "test_repros/round2/m02_top_ifmain.pyc",
  "pyc_sha256": "...",
  "pyc_present": true,
  "pyc_loadable": null,
  "input_model": {"kind": "module", "calls": [], "seed": 0},
  "entrypoint": "module",
  "host_prelude": null,
  "host_prelude_reason": "...",
  "counterexample_hint": "...",
  "excluded": []
}
```

顶层新增：

```json
{"j_schema_version": "v2", "generator_version": "2.0.0",
 "generator_sha256": "...", "seed": 0, "excluded": []}
```

`p_j`/`pyc` 是仓根相对路径；`p_j_sha256`/`pyc_sha256` 由生成时实际文件计算。`pyc_loadable` 只有检查器实际 `marshal.loads` 后才置真，生成器不代填。`input_model` 目前是默认模块模型；更强的调用模型必须由 C4 证据记录说明，不能从默认值推断。

生成确定性：同一输入连续运行两次，`judgment_space.json` 的 sha256 相同（本轮为 `1e2aad199016b0a6f415a190e315818bfc3705123a1ed0fad49544bacec404fe`；生成器 sha256 为 `172341e294f4c384ee5e9a8a2eb8d077e4d5391df0668119680073dcbc7d42e1`）。

## 3. C1–C5 判定

检查器逐条验证：

| 条件 | 检查 |
|---|---|
| C1 | `p_j` 存在、非空、行数 > 0、实际 sha256 == `p_j_sha256` |
| C2 | `pyc` 存在、实际 sha256 == `pyc_sha256`、magic 匹配、`marshal.loads` 成功 |
| C3 | 证据记录的 `c3.product_path` 存在、非空、hash 匹配、`command` 非空 |
| C4 | `c4.verdict ∈ {EQUAL, DIFFERENT, INCONCLUSIVE, ERROR}`，有 `seed` 与整型 `exit_code` |
| C5 | 同一记录的 `source/pyc/product` 三个 hash 分别等于 C1–C3；`judge_sha256` 为 64 hex（若传 `--judge` 则与实文件比对）；`runner_version` 非空 |

`covered_5tuple` 只在 C1–C5 全部通过时成立。`DIFFERENT` 仍算 `covered_5tuple`，但计入 `semantic_failures`，不算 `green`；`INCONCLUSIVE`/`ERROR` 归 `inconclusive`，绝不计为 covered。

## 4. 分类

| 状态 | 条件 |
|---|---|
| `excluded` | 条目/记录显式排除 |
| `n/a` | 条目/记录显式 n/a |
| `uncovered` | C1 失败，或 C2–C4 已成立但 C5 失败 |
| `probe_only` | C1 成立，但 C3 产物或 C2 pyc 缺失，无法进入 C4 |
| `unexecuted` | C1–C3 成立，但 C4 缺失 |
| `inconclusive` | C4 verdict 为 INCONCLUSIVE/ERROR |
| `covered_5tuple` | C1–C5 全通过 |

`uncovered[]` 输出所有非 `covered_5tuple` 条目及 `reason`；`uncovered` 总数 = `J_total - covered_5tuple`。这使 `probe_only`、`unexecuted`、`n/a`、`inconclusive`、`excluded` 都不可能被误读为覆盖。

## 5. 真实读数

命令：

```text
python -X utf8 tools/completeness/jspace_generator.py \
  --evidence-root .trae/specs/attain-true-completeness/rounds \
  --out .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --md .trae/specs/attack-completeness-claims/rounds/round9/JUDGMENT_SPACE.md

python -X utf8 tools/completeness/coverage_checker.py \
  --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --out .trae/specs/attack-completeness-claims/rounds/round9/COVERAGE_C1C5.md \
  --json .trae/specs/attack-completeness-claims/rounds/round9/coverage_c1c5.json \
  --allow-uncovered
```

读数：

| 指标 | 值 |
|---|---:|
| `J_total` | 1556 |
| `covered_5tuple` | **0** |
| `probe_only` | 1168 |
| `unexecuted` | 0 |
| `n/a` | 0 |
| `inconclusive` | 0 |
| `excluded` | 0 |
| `uncovered` | **1556** |
| `coverage_pct` | **0.00%** |
| `semantic_failures` | 0 |
| `green` | 0 |

未覆盖原因分布：

| status | reason | 数量 |
|---|---|---:|
| `probe_only` | `c3_product_missing` | 1168 |
| `uncovered` | `c1_source_missing` | 388 |

解释：

- 1168 条已有源与 pyc（C1/C2 可过），但没有 C3 产物、C4 执行判定与 C5 哈希链，因此只能算 probe-only；
- 388 条连源文件都不存在（典型是只登记了 `.pyc` 或路径为代码站点），C1 直接失败；
- 当前没有真实的 C3/C4/C5 证据，所以 G1 仍**不可评**；不能把 1556 当分母、0 当分子以外的任何数字写成「覆盖」。
- 旧 `976/1556` 与新的 `0/1556` 不是矛盾，而是两种口径：前者只验登记，后者验五元组。

## 6. 合成自测

`coverage_checker_selftest.json`：13/13 checks 通过，覆盖一个正例和多个反例：

| 用例 | 期望 | 实际 |
|---|---|---|
| 完整 C1–C5，EQUAL | `covered_5tuple` + green | 通过 |
| 完整 C1–C5，DIFFERENT | `covered_5tuple` + semantic_failure | 通过 |
| 无证据，C1/C2 有 | `probe_only` | 通过 |
| 有 C1–C3，无 C4 | `unexecuted` | 通过 |
| 显式 n/a | `n/a` | 通过 |
| C4=INCONCLUSIVE | `inconclusive` | 通过 |
| 显式 excluded | `excluded` | 通过 |
| 源缺失 | `uncovered` | 通过 |
| C5 source hash 被篡改 | `uncovered` / `c5_chain_mismatch` | 通过 |
| 门禁 | `uncovered > 0` 退出 1 | 通过 |

自测同时验证：C2 会真的 `marshal.loads`，C5 会真的比对三个 hash；不是只检查字段存在。

## 7. 边界与后续

1. 本轮没有 C3/C4/C5 生产者；`coverage_checker` 只是消费证据，不伪造证据。真实 C1–C5 覆盖要等 Task 9.6 把反编译产物与 `semantic_diff` 判定写入同一证据记录。
2. `input_model` 默认是模块模型；对需要特定调用才能到达 body 的条目，C4 会产生 `INCONCLUSIVE`，不能靠默认模型刷绿。
3. `pyc_loadable` 只在检查器运行时计算；生成器写 `null`，避免把「文件存在」冒充「可加载」。
4. J v1 的 1556 分母保持不变；schema v2 只增加绑定字段，不新增/删除条目。新增语法仍走 J v2 的独立版本，不得改写 1556。
5. 388 条 C1 缺失是真实缺口，不是统计噪声；其中多数为只有 pyc 的探针。补源或显式排除必须逐条登记，不能静默补路径。
6. `host_prelude` 目前为 `null` 并记录原因；它尚未由生成器构造，属于 J 充分性审查的未完成项，不能写成「已装配」。

## 8. 退出码

- `0`：`covered_5tuple == J_total`；
- `1`：存在任何非 `covered_5tuple` 条目（默认门禁）；
- `2`：清单/证据/判据文件无法读取。
