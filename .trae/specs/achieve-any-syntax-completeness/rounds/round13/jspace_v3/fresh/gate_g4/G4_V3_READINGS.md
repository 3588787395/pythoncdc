# G4 v3（谓词感知口径）实测读数

**状态：预演读数 + 分档证据，全部「需评审」；本文不宣称 G4 通过。**
v1 草案定义见 [`G4_PROOF_THEORY.md`](G4_PROOF_THEORY.md)，v1 读数见 [`G4_V1_READINGS.md`](G4_V1_READINGS.md)。
本轮只做三件事：**按当前树重建 universe**、**让 traces 记谓词实测结果而不是锚点到达**、
**用 v3 口径重跑 v1 校验器**；外加把 `empty_cov_true` 按锚点归属分成 D1/D2/D3
（[`G4_V2_TRIAGE.md`](G4_V2_TRIAGE.md)）。

`manifest_v2.json` / `universe_v2.json` / `traces_v2.json` / `trace_g4_current.py` /
`rule_manifest.py` / `rule_universe.py` / `core/` / `scripts/` / `tests/` **均未改动**（见 §7）。

---

## 1. 摘要

| 项 | v1（漂移快照，锚点口径 traces） | **v3（当前树，谓词口径 traces）** |
|---|---|---|
| 规则全集（分母） | 344 | **344** |
| universe occurrences | 5894 | **5896** |
| 运行次数 / J 条目 | 131 / 1556 | **131 / 1556** |
| 运行失败 pyc | 0 | **0** |
| `rules_hit`（traces 记命中） | 244（锚点到达） | **156（谓词实测为真）** |
| `empty_cov` | 100 | **188（= 从未为真）** |
| proved | 119 | **127** |
| open | 225 | **217** |
| 预演 `rule_manifest --check` | `ready=119/344`、`empty_cov=100`、FAIL | **`ready=127/344`、`empty_cov=188`、FAIL** |

> 一句话：**换到谓词感知口径后，`rules_hit` 从 244 降到 156，`empty_cov` 从 100 升到 188。**
> 少的 88 条正是「锚点行到达、谓词恒假」的规则；多出来的 88 条同样是它们——差别只是
> 旧口径把它们算作"命中"。此外重建 universe 让 13 条规则第一次被测到真谓词（143→156）。

---

## 2. 任务一：按当前树重建 universe（机械步骤）

```powershell
D:/Python/python.exe -X utf8 tools/completeness/rule_universe.py `
  --code core/cfg --json fresh/gate_g4/universe_v3.json
# [rule_universe] total_rules=344 files=20 kinds={"isinstance_ast": 15, "opcode_eq": 329}
```

### 2.1 与 `universe_v2` 的差异

| 项 | 读数 |
|---|---|
| 规则数 | 344 → **344**（新增 0 / 消失 0，`rule_id` 集合完全相同） |
| occurrences | 5894 → **5896**（+2，全在 `region_analyzer.py`：690 → 692） |
| 锚点集合完全相同的规则 | 209 |
| 锚点发生迁移的规则 | **135**（其中 **32** 条与旧锚点**零交集**，即 v1 报告里"完全失去锚点"的 32 条） |
| 不同锚点位置数（去重字符串） | 2522 → 2523；旧锚点里 **496** 个位置在 v3 中不存在 |
| 按 occurrence 加权的失效锚点 | **1159 / 5894 = 19.7%**（`region_analyzer.py` 161、`region_ast_generator.py` 998） |
| 源文件 sha256 变化 | 2 个：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py` |

- v1 报告写的「1209/5894 锚点失效」用的是"该行还在但已无该谓词"的口径，本轮按
  "锚点字符串是否仍被声明"机械计数得 **1159**，两者同一量级、同一结论：
  **v1 的 proved 数是在漂移快照上测的，不可与 v3 直接比。**
- 重建后：`anchors_located = 344/344`、`rules_not_located = 0`、`rules_with_source_drift = 0`
  （v1 是 32 条 `predicate_not_located`、106 条 `anchor_source_drift`）。
- 差异明细：`D:\temp\opencode\cl_layout\g4v2\universe_diff_v2_v3.json`、
  `anchor_drift_occurrences.json`。

---

## 3. 任务二：`traces_v3.json` 记「谓词实测结果」

新文件 `fresh/gate_g4/trace_g4_v3.py`（**不改**既有 tracer）。它 **import**
`tools/completeness/rule_proof_check.py` 复用其谓词重建与求值逻辑
（`build_rule_index` / `_scan_file` / `Measurer`），只负责驱动 131 次运行 + 记录
"哪些规则的谓词在某次运行里实测为真"。

输出 `traces_v3.json`：1556 条记录，每条
`{entry_id, rules_true, rules_false, rules_evaluated, rule_ids, pyc}`，
其中 `rule_ids = rules_true`（下游 `rule_manifest` / `rule_proof_check` 读这个字段，
所以「命中」的定义在文件格式层面就被改成**谓词为真**）。

| 读数 | 值 |
|---|---|
| 记录数（J 条目） | 1556 |
| distinct pyc / 运行失败 | 131 / 0 |
| `rules_hit_true`（至少一次谓词为真） | **156 / 344** |
| `empty_cov_true`（从未为真） | **188** |
| 谓词被求值过的规则 | 244（另有 100 条规则零求值） |
| 求值总次数 / 其中为真 | 1,920,617 / **6,375（0.33%）** |
| (entry, rule) 真命中对 | 77,199 |
| (entry, rule) 假命中对 | 229,699 |

### 3.1 与 `traces_v2`「锚点命中」的差值

| 对比项 | 读数 |
|---|---|
| `traces_v2.rules_hit`（锚点到达） | **244** |
| `traces_v3.rules_hit_true`（谓词为真） | **156** |
| 规则级差值 | **−88** |
| `(run, rule)` 对：v2 记命中但该次运行谓词**从未为真** | **12,769**（v1 同口径为 13,521，同一量级） |
| `(run, rule)` 对：v2 记命中且谓词为真 | 4,861 |
| `(run, rule)` 对：谓词为真但 v2 没记命中 | 0（v3 真集 ⊆ v2 命中集，自洽） |
| `(entry, rule)` 对：v2 全部命中 | 231,827 |
| 其中谓词实测为真 | 77,199（**33.3%**） |
| 其中只是"锚点行到达" | **154,628（66.7%）** |

- 12,769 与 v1 的 13,521 差 752，来源可解释：重建 universe 让 135 条规则换锚点，
  其中 13 条规则第一次被测到真谓词（143 → 156），它们在 v2 口径下贡献的"假命中"对随之消失。
- 最热的假命中（131 次运行全部"命中"、谓词 100% 为假）：
  `__NESTED_FUNC__`@`code_generator.py:4115`（求值 14,871 次）、
  `CACHE`@`ast_generator_v2.py:2666`（72,749 次）、
  `RETURN_CONST`@`ast_generator_v2.py:1877`（59,342 次）、
  `LOAD_CONSTANT`@`ast_generator_v2.py:1062`（49,826 次）、
  `LOAD_CLASSDEREF`@`ast_generator_v2.py:1103`（40,758 次）。
- 运行期清单 `executed_inventory_v3.json`：16 个锚点文件里 **12 个**在 131 次运行中
  真被执行过；`patch_detector.py`、`patch_detector_enhanced.py`、
  `objective_patch_detector.py`、`exception_handler.py` 一次都没有。

---

## 4. 任务三：用 v3 口径重跑 v1 校验器

```powershell
D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py `
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_v3.json `
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces  fresh/gate_g4/traces_v3.json `
  --out fresh/gate_g4/proof_records_v2.json `
  --manifest-out fresh/gate_g4/manifest_proved_v2.json
```

`manifest_v3.json` = 用 `rule_manifest.py --generate` 从 `universe_v3` 生成的**基线清单**
（344 条全 open、无 witness），只作 `rule_proof_check` 的输入底座；校验器不会改它，
只输出候选清单 `manifest_proved_v2.json`。

### 4.1 proved / open

| 项 | v1 | **v3** |
|---|---|---|
| proved | 119 | **127** |
| open | 225 | **217** |
| 正 witness（实测为真的发生点） | 143 | **156** |
| 严格负 witness | 119 | **127** |
| 运行耗时（pipeline） | 170.8 s | 215.3 s |

### 4.2 open 的主因分布（互斥，合计 217）

| 原因码 | v1 | **v3** | 含义 |
|---|---|---|---|
| `no_occurrence_in_J` | 96 | **100** | 谓词可重建，但锚点在 J 中**一次都没执行** ⇒ 零求值 |
| `predicate_false_at_site` | 73 | **88** | 锚点行执行了，但谓词**每一次都为假** |
| `negative_witness_missing` | 24 | **29** | 有正 witness，缺"另一条目里位置到达且谓词全假"的严格负 witness |
| `predicate_not_located` | 32 | **0** | 锚点已重建，全部可定位 |

- `100 + 88 = 188` = `empty_cov_true`；`127 + 29 = 156` = 至少一次为真的规则数。
  两个恒等式都在 `proof_records_v2.json` 里逐条可查，`open_reasons` 与
  `measurement` 字段互相自洽。
- **「其它」= 0**：217 条 open 全部落在上面三类里，没有 `predicate_not_located`、
  没有 `trace_runtime_disagreement`（v3 traces 只记实测真值，结构上不可能出现该码）。

### 4.2.1 proved 见证质量自洽审计（127 条逐条复算，0 处违规）

| 检查 | 结果 |
|---|---|
| `proof_id` 可由 6 字段重算一致、`hash_input` 一致 | 127 / 127 |
| 正/负 witness 非空且 id ∈ J | 127 / 127 |
| 负 witness 与正 witness **不同 pyc** | 127 / 127 |
| 正 witness 证据 `predicate_result=true`、负 witness `=false` | 127 / 127 |
| `composition` 非空且成员都在 universe 内、`semantic_domain.hosts/depths` 非空 | 127 / 127 |
| `composition == ["<singleton>"]` | 0 条 |
| proved ⊆ 实测为真集合 | 127 / 127 |
| `manifest_proved_v2.json`：open 且带 `proof_id` | **0 条**（127 个 proof_id 全属于 proved） |
- 叠加标记：`rules_without_any_occurrence = 100`、`rules_with_false_only_site = 88`、
  `negative_witness_weak_only = 21`（若评审接受"弱负 witness"，proved 会是 **148**，仅为敏感性参考，
  **未写入候选清单**）。

### 4.3 预演 `rule_manifest --check`（外部 CLI，与工具内预演逐字一致）

```powershell
D:/Python/python.exe -X utf8 tools/completeness/rule_manifest.py --check `
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_proved_v2.json `
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces  fresh/gate_g4/traces_v3.json
# total_rules=344 manifest=344 unmapped=0 orphan=0 proved=127 open=217
# empty_cov=188 G4=FAIL reason=mapping_or_proof_gap
```

| 字段 | 读数 |
|---|---|
| `total_rules` / `manifest_rules` | **344 / 344** |
| `unmapped_anchors` / `orphan_rules` / `anchor_orphans` | 0 / 0 / 0 |
| `proved` | **127** |
| `ready_proved` | **127** |
| `not_ready_proved` / `witness_errors` / `domain_errors` | 0 / 0 / 0 |
| `empty_cov` | **188** |
| `g4` / `reason` | **FAIL** / `mapping_or_proof_gap` |

- **`ready/total = 127/344`，`empty_cov = 188`，G4 = FAIL。** 按 `rule_manifest.py:190-195`
  的判据，即使 344 条全部 proved，只要 `empty_cov != 0` 仍判 FAIL。
- 自洽性检查：v3 口径下 `trace_runtime` 三个反向计数全为 0
  （traces 只记实测真值 ⇒ 不可能出现"记了命中却没求值"）；v1 是
  `traced_rules_never_measured_true = 13,521`。

### 4.4 明确回答

| 问题 | 答案 |
|---|---|
| 换到谓词感知口径后 `rules_hit` 从 244 变成多少？ | **156**（−88） |
| `empty_cov` 从 100 变成多少？ | **188**（+88） |

两个数字是同一批 88 条规则的两面：旧口径按"锚点行到达"记命中，新口径要求"谓词实测为真"。

---

## 5. 任务四：`empty_cov_true` 按锚点归属分档

详见 [`G4_V2_TRIAGE.md`](G4_V2_TRIAGE.md)。结论：

| 档 | 条数 | 判据要点 |
|---|---|---|
| **D1 无 importer** | **15** | 锚点模块在 live 链上 0 importer 且运行期从未被执行（`objective_patch_detector.py` 11 条、`patch_detector.py` 4 条；正是 v1 §5.1 的 15 条 `isinstance_ast`） |
| **D2 类/函数从不构造、从不执行** | **60** | 模块在链上，但锚点所在函数/方法 131 次运行中零执行、规则谓词零求值（`ASTGeneratorV2` 27 条——该类从未被实例化；`CodeGenerator._generate_dict_node` 16 条——类被构造但 dict 分支从不走；`StructuredAnalyzer` 7 条；其余 10 条） |
| **D3 可达但无输入触发** | **113** | 至少一个锚点所在函数执行过，谓词仍从未为真；其中 88 条"行到达、谓词恒假"，25 条"分支未走到" |

- D1/D2 是**分母/调用链问题**（要么把这些模块排除出 G4 分母并写明理由，要么让 live 链真的走到），
  D3 是**输入覆盖问题**（加 J 条目），三类不能合并成一个数字。

---

## 6. 本轮产物

| 文件 | 内容 |
|---|---|
| `fresh/gate_g4/universe_v3.json` | 按当前树重建的规则全集（344 / 5896，20 文件） |
| `fresh/gate_g4/trace_g4_v3.py` | **新增**谓词感知 tracer（import `rule_proof_check` 的谓词逻辑） |
| `fresh/gate_g4/traces_v3.json` | 1556 条：`rules_true` / `rules_false` / `rules_evaluated` / `rule_ids=rules_true` |
| `fresh/gate_g4/executed_inventory_v3.json` | 锚点文件在 import 阶段 + 131 次运行中真执行过的 code object |
| `fresh/gate_g4/manifest_v3.json` | 由 `rule_manifest.py --generate` 从 universe_v3 生成的**基线**清单（派生中间件） |
| `fresh/gate_g4/proof_records_v2.json` | v3 口径逐条记录（344 条：status / proof / witnesses / reasons / measurement） |
| `fresh/gate_g4/manifest_proved_v2.json` | 由 `manifest_v3.json` 派生的候选清单（`v1_candidate` 标记，未合并） |
| `fresh/gate_g4/G4_V2_TRIAGE.md` | D1/D2/D3 分档（含 importer / 类级 / 函数级证据） |
| `fresh/gate_g4/G4_V3_READINGS.md` | 本文件 |
| `D:\temp\opencode\cl_layout\g4v2\` | 上述文件的镜像 + 差异/分档中间产物（`universe_diff_v2_v3.json`、`anchor_drift_occurrences.json`、`triage_v3.json`、`rule_coverage_v3_rehearsal.json`） |

---

## 7. 纪律自查

| 约束 | 状态 |
|---|---|
| 不改 `core/`、`scripts/`、`tests/` | ✅ `git status` 无这些路径的改动 |
| 不改 `rule_manifest.py`、`rule_universe.py` | ✅ 只读调用（`--generate` / `--check`） |
| 不改 `TOLERANCE_REGISTRY.md` | ✅ 未触碰 |
| 不改 `manifest_v2.json` / `universe_v2.json` / `traces_v2.json` | ✅ 只读；v3 全部是新文件 |
| 只新增 `trace_g4_v3.py` 一个脚本 | ✅（`rule_proof_check.py` 本身未修改） |
| 不引入数字上限 / 不采样 | ✅ 344 条规则、131 个 pyc、1556 条 J 条目全量；无 depth cap、无 top-N |
| 谓词只读结构（isinstance/opcode），不做名字/常量/偏移门控 | ✅ 谓词由 universe 的 `kind+symbol` 在锚点处重建；`bytecode_offset` 只出现在 `occurrence_id` |
| 不把任何规则写成 proved 后宣称 PASS | ✅ `ready=127/344`、`empty_cov=188`、`G4=FAIL`，全部标注需评审 |

---

## 8. 复现（cwd = `F:\Downloads\pythoncdc-main`，解释器 `D:/Python/python.exe -X utf8`）

```powershell
# 1) universe
D:/Python/python.exe -X utf8 tools/completeness/rule_universe.py --code core/cfg `
  --json fresh/gate_g4/universe_v3.json

# 2) 谓词感知 traces（约 4 分钟，131 次运行）
D:/Python/python.exe -X utf8 fresh/gate_g4/trace_g4_v3.py `
  --universe fresh/gate_g4/universe_v3.json `
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces-v2 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/gate_gap/traces_v2.json `
  --out fresh/gate_g4/traces_v3.json `
  --inventory-out fresh/gate_g4/executed_inventory_v3.json

# 3) 基线清单 + 用 v3 口径重跑校验器
D:/Python/python.exe -X utf8 tools/completeness/rule_manifest.py --generate `
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_v3.json
D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py `
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_v3.json `
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces  fresh/gate_g4/traces_v3.json `
  --out fresh/gate_g4/proof_records_v2.json `
  --manifest-out fresh/gate_g4/manifest_proved_v2.json

# 4) 预演（外部 CLI）
D:/Python/python.exe -X utf8 tools/completeness/rule_manifest.py --check `
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_proved_v2.json `
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces  fresh/gate_g4/traces_v3.json

# 5) 分档
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4v2\triage_g4.py
```
