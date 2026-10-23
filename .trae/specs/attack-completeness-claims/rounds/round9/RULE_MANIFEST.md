# Task 9.4 独立规则全集、规则清单与覆盖引理

> 状态：Task 9.4 **工具与真实读数已完成**；Task 9.5–9.7 未开始。
> **不声称 G4 通过，不声称规则完备，不声称语料完备或 J 门槛达标。**
> 本文件只记录独立枚举、清单映射、对账和当前缺口。

## 1. 交付物

| 文件 | 作用 |
|---|---|
| `tools/completeness/rule_universe.py` v1.0.0 | 从 `core/cfg/**` 静态枚举独立规则全集，不读取 manifest |
| `tools/completeness/rule_manifest.py` v1.0.0 | 生成/检查 manifest，双向对账，计算 G4 与规则覆盖引理 |
| `tools/completeness/rule_manifest.json` | 339 条规则映射；当前全部 `open` |
| `rounds/round9/rule_universe.json` | 真实独立枚举结果（339 条，5663 个分支位置） |
| `rounds/round9/rule_coverage.json` | 真实对账/覆盖读数（G4 `INCONCLUSIVE`） |
| `rounds/round9/rule_manifest_selftest.json` | 合成正/反例自测 12/12 |

实现契约：

```text
python -X utf8 tools/completeness/rule_universe.py --code core/cfg \
    --json .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json
python -X utf8 tools/completeness/rule_manifest.py --generate \
    --universe .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json \
    --manifest tools/completeness/rule_manifest.json
python -X utf8 tools/completeness/rule_manifest.py --check \
    --universe .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json \
    --manifest tools/completeness/rule_manifest.json \
    --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
    --json .trae/specs/attack-completeness-claims/rounds/round9/rule_coverage.json
```

`--check` 退出码：`0=PASS`，`1=FAIL`，`2=INCONCLUSIVE`。本次真实运行退出码为 `2`。

## 2. 独立规则全集

枚举器只读 `core/cfg/**/*.py` 的 AST，不读 `rule_manifest.json`，因此 `total_rules` 不是 manifest 自证分母。识别的分派形态：

- `isinstance(x, ast.X)`（含 `ast.X` 元组）；
- `opname/opcode/name/kind/node_type/node_name == "X"`；
- `X in ("A", "B", ...)` 形式的分派集合；
- `node.__class__.__name__ == "X"` / `type(node).__class__.__name__ == "X"`；
- 目标名含 `region` 的元组/列表/集合赋值中的区域类型常量。

同一 `(kind, symbol)` 的多个源码位置合并为一条规则；`anchors` 保留全部位置，`occurrences` 保留分支数。规则 ID 为 `RULE-` + `sha256(kind|symbol)[:12]`，不依赖行号，源码位移不会改变 ID。

### 2.1 真实读数

| 指标 | 读数 |
|---|---:|
| 扫描文件 | 20 |
| 独立规则数 `total_rules` | **339** |
| 分支位置 `total_occurrences` | 5663 |
| `isinstance_ast` | 15 |
| `opcode_eq` | 324 |
| `region_type` / `class_name_eq` / 其他 | 0 |

文件分布（位置数）：

| 文件 | 分支位置 | 文件 | 分支位置 |
|---|---:|---|---:|
| `region_ast_generator.py` | 2455 | `region_analyzer.py` | 666 |
| `ast_generator_v2.py` | 1495 | `structured_analyzer.py` | 519 |
| `comprehension_generator.py` | 174 | `pattern_parser.py` | 128 |
| `code_generator.py` | 95 | `exception_handler.py` | 83 |
| `patch_detector.py` | 17 | `objective_patch_detector.py` | 16 |
| `cfg_builder.py` | 5 | `peephole_patterns.py` | 4 |
| `patch_detector_enhanced.py` | 3 | `ast_converter.py` / `basic_block.py` / `dominator_analyzer.py` | 各 1 |
| `__init__.py` / `cfg_optimizer.py` / `cfg_visualizer.py` / `opcode_feature_detector.py` | 0 | | |

`universe_sha256 = 59151f4e42bb444db1659975cc58fd0cf1473e5aa7beb4e59581c2a20c462b2f`；扫描器自身 sha256 前 16 位 `2858c3bc2ad8d648`。

### 2.2 与 B178/B183 的 191/174/123 口径

历史记录出现 191/174/123 三个规则计数，含义未完全统一。本轮**不以任一历史数字回填分母**：独立枚举按上述 `(kind, symbol)` 定义得到 339 条，与 191/174/123 均不一致。差异保留为待登记口径问题，Task 10 台账须说明每个数字的来源（标记数 / manifest 条目 / 独立分派符号）；在此之前不得把 174 或 191 写成 G4 的 `total_rules`。

## 3. Manifest 与双向对账

`tools/completeness/rule_manifest.json` 每条规则含：

```text
rule_id, universe_id, anchor, anchors, pattern, patterns,
preconditions, effect, guards, invariants,
semantic_domain, witnesses, composition, proof, status
```

初始状态全部为 `open`；`witnesses` 正/反例为空、`semantic_domain` 的 `hosts/depths` 为空、`composition` 为空、`proof.proof_id` 为 `null`。这是如实的未证明状态，不是通过状态。

真实对账读数：

| 指标 | 读数 |
|---|---:|
| manifest 条目 | 339 |
| `total_rules`（来自 universe） | 339 |
| `unmapped_anchors` | **0** |
| `orphan_rules` | **0** |
| `anchor_orphans` | 0 |
| `proved` | **0** |
| `tested-only` | 0 |
| `open` | **339** |
| `ready_proved` | 0 |
| `not_ready_proved` | 0 |
| `coverage_evaluable` | false（未提供 `--traces`） |
| `empty_cov` | null |
| **G4** | **INCONCLUSIVE** |
| `reason` | `no_rule_traces` |

对账为 0 只表示**映射完整**；不表示规则已证明。即使未来提供 `--traces`，当前 339 条全 `open` 也会使 G4 为 `FAIL`（`not_all_proved`），不会自动通过。

## 4. 覆盖引理

`rule_manifest.py --check` 的 `Cov(R_i)` 来自显式 `--traces`：每个 trace 记录 `entry_id` 与触达的 `rule_ids`（也接受 `{entry_id: [rule_ids]}` 映射）。`empty_cov` 是触达为空的规则数。

- 无 `--traces`：`coverage_evaluable=false`，G4 `INCONCLUSIVE`，不得把缺失轨迹当成 100%。
- 有 `--traces` 但任一规则 `Cov=∅`：G4 `FAIL`。
- 每条 `proved` 规则必须同时有正例、反例、`semantic_domain.hosts/depths`、`composition`、`proof.proof_id`；缺一即计入 `not_ready_proved`，G4 不通过。
- `unmapped_anchors>0` 或 `orphan_rules>0`：G4 `FAIL`。
- `total_rules=0`：G4 `INCONCLUSIVE`（`empty_universe`），不是 0/0 通过。

当前没有规则轨迹生产者；Task 9.5/9.6 才把 fuzz/语料执行轨迹接入。因此现在只能交付**分母、映射和检查器**，不能交付覆盖通过结论。

## 5. 合成自测

`rule_manifest_selftest.py` 在临时目录构造两条规则，验证 12 项：

| 检查 | 结果 |
|---|---|
| 独立扫描计数（2 条 / 2 位置） | PASS |
| 两次扫描确定性 | PASS |
| manifest 生成 2 条 | PASS |
| 全 proved + 全轨迹 → G4 PASS | PASS |
| `ready_proved=2`、`empty_cov=0` | PASS |
| 无 traces → INCONCLUSIVE | PASS |
| orphan → FAIL | PASS |
| unmapped → FAIL | PASS |
| 全 open → FAIL | PASS |
| 空 universe → INCONCLUSIVE | PASS |

自测输出：`rounds/round9/rule_manifest_selftest.json`。它只证明检查器行为正确，不证明真实 `core/cfg` 规则。

## 6. 边界与未完成

1. 静态枚举是**语法层**的：`isinstance`/字符串比较/区域常量能识别，动态注册表、经变量间接分派、反射式分派可能漏计；漏计会低估 `total_rules`，Task 10 须用运行时轨迹交叉检查。
2. `opcode_eq` 将任何目标名等于 `opname/opcode/name/kind/node_type/node_name` 的字符串比较视为分派；可能包含少量非规则比较，当前按保守全集保留，不静默删除。
3. 339 与 191/174/123 的差异未消解；不得为了让数字好看而改扫描器或改 manifest。
4. 规则证明、正/反例、H×D 域见证、guard 负例、O6 组合见证全部未产出；G4 未通过。
5. 真实 `rule_coverage.json` 的 `coverage` 为空映射、`empty_cov=null`，因为没有 `--traces`；Task 9.5/9.6 接入后才可计算。
6. 本任务未修改 `core/cfg/**`、`scripts/pyc_verify.py`、`tests/**`、`wiki/**`、`rules.md`；402 认证产物未重跑，零回退结论沿用已签收基线。

## 7. 下一步

- Task 9.5：`fuzz_driver.py` + 最小化 + 24 条隐藏金丝雀；生成规则轨迹与反例候选。
- Task 9.6：把 `rule_universe`/`rule_manifest`/`coverage_checker`/`semantic_diff`/`mutation_test` 接入 E 门禁，输出 G1–G6 与双读数。
- Task 10：封闭/挂账 B163–B219、U-01–U-06，登记 191/174/123/339 口径差异，完成终验。
