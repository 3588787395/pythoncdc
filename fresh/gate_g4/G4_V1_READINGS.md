# G4 v1（草案定义）实测读数

**状态：预演读数，不是 G4 通过与结论。** 定义见 [`G4_PROOF_THEORY.md`](G4_PROOF_THEORY.md)（v1，待评审）。
`manifest_v2.json` 未被改动；`manifest_proved_v1.json` 只是候选增量文件。
所有数字均由 `tools/completeness/rule_proof_check.py` 一次完整运行产出，可用第 7 节命令复现。

---

## 1. 摘要

| 项 | 读数 |
|---|---|
| 规则全集（分母） | **344** |
| 按 v1 定义 **proved** | **119** |
| **open** | **225** |
| 正 witness（实测为真的发生点条目） | 143 |
| 严格负 witness | 119 |
| 运行次数 / J 条目 | 131 个 distinct pyc / 1556 条 |
| 谓词实测求值总次数 | 1,491,937 |
| 运行失败 pyc | 0 |
| 耗时 | pipeline 170.8 s，进程总 183.8 s |

> 一句话：**119 条规则有"谓词在具体发生点为真 + 在另一条目上实测为假"的完整见证；225 条没有，
> 其中 100 条根本没有发生点、73 条位置到达但谓词从不成立、24 条缺严格负 witness、32 条锚点
> 已漂移无法定位谓词。**

---

## 2. open 的原因分布

### 2.1 主因（互斥，合计 = 225）

| 原因码 | 条数 | 含义 |
|---|---|---|
| `no_occurrence_in_J` | **96** | 谓词可重建，但该规则的锚点行在任何 J 条目中都不执行 ⇒ 无发生点、无 witness |
| `predicate_false_at_site` | **73** | 锚点行被执行（traces 记为"命中"），但谓词在**每一次**求值上都为假 ⇒ 谓词实测不成立 |
| `negative_witness_missing` | **24** | 有正 witness，但找不到"另一个条目里位置到达且谓词全假"的严格负 witness |
| `predicate_not_located` | **32** | 声明的锚点位置已无该谓词（源漂移），无法重建谓词 ⇒ 无法实测 |

### 2.2 叠加标记（非互斥，只作诊断）

| 标记 | 条数 | 说明 |
|---|---|---|
| `no_occurrence_in_J`（含叠加） | 128 | 零次求值的规则总数（见 2.3） |
| `anchor_source_drift` | 106 | 该 open 规则的 `source_files` 中至少一个文件 sha256 与 universe 快照不一致 |
| `trace_runtime_disagreement` | 28 | traces 记为命中，但实测中该规则位置从未被求值（27 条锚点已漂移、1 条该行未被实测执行） |
| `predicate_false_at_site` | 73 | 锚点行到达但谓词从未为真（与主因是同一批规则） |

### 2.3 与 traces 口径 `empty_cov = 100` 的对应关系

```
零次求值 128 条 = 100（无任何 trace 覆盖，含 15 条 isinstance_ast 家族）
                + 27（有 trace 覆盖，但锚点漂移 ⇒ 谓词不可定位、零求值）
                +  1（有 trace 覆盖、锚点可定位，但该行在实测运行中从未被执行）
```

- 100 条无 trace 覆盖里：95 条谓词可定位但从不执行，5 条同时还不可定位。
- `traces` 口径的 100 = 95 + 5，本校验器独立测得的 empty_cov 集合与 traces 完全一致
  （`g4_check_rehearsal.empty_cov_rules` 与 traces 的 empty_cov 集合逐 id 相同）。
- 所以「无发生点 100 条」被本次实测确认；额外冒出的 28 条不是"无发生点"，而是
  **有行命中、锚点已失效**（27 条）或**有行命中、行却未被执行**（1 条），详见第 5 节。

### 2.4 主因 × 是否被 traces 记为命中

| 类别 | 被 traces 记为命中 | 未被命中 | 合计 |
|---|---|---|---|
| proved | 119 | 0 | 119 |
| `predicate_false_at_site` | 73 | 0 | 73 |
| `negative_witness_missing` | 24 | 0 | 24 |
| `predicate_not_located` | 27 | 5 | 32 |
| `no_occurrence_in_J` | 1 | 95 | 96 |
| **合计** | **244** | **100** | **344** |

即 traces 的 `rules_hit = 244` 由 119 条 proved + 125 条 open 组成；在这 125 条里，
**97 条（73 + 24）在"行命中"之外从未产生过真正的谓词匹配**。`no_occurrence_in_J` 行里的
那 1 条命中是"traces 记了命中、锚点也可定位，但实测运行中该行从未被执行"的
`trace_runtime_disagreement` 个例。

---

## 3. proved 规则的见证质量（自洽审计）

对 119 条 proved 逐条复算，0 处违规：

| 检查 | 结果 |
|---|---|
| `proof_id` 可由 6 个字段重算一致 | 119 / 119 |
| `hash_input` 与记录字段一致 | 119 / 119 |
| `witnesses.positive`、`witnesses.negative` 均非空且 id ∈ J | 119 / 119 |
| 正 witness 在 traces 中确实给该规则记过命中 | 119 / 119 |
| 负 witness 与正 witness **不同 pyc**（不许同一次执行冒充反例） | 119 / 119 |
| 负 witness 的谓词实测为 `false` 且该位置到达 | 119 / 119 |
| `composition` 非空且成员 id 全在 universe 内 | 119 / 119 |
| `semantic_domain.hosts` / `depths` 非空 | 119 / 119 |
| `composition` 为 `["<singleton>"]` | 0 条 |

负 witness 选取分布：`same_form_host` 77、`same_form` 24、`any` 18。
`composition` 规模 10–79 条规则；`semantic_domain.hosts` 3–48 个、`depths` 1–3 个
（3 个 depth 全含 107 条，2 个 8 条，1 个 3 条）。

关于 open 规则的两个一致性约定（都已实测核对）：

- **open 规则不携带 `proof_id`**（`manifest_proved_v1.json` 中 open 且 `proof_id` 非空 = 0 条）。
  24 条"有正 witness、缺严格负 witness"的 open 规则，其已测到的发生点保存在
  `v1_draft.partial_positive_occurrence`，只是**证据**，不是 proof——避免有人手工把 status
  改成 proved 就白拿 `ready`。
- **从未被实测为真的 open 规则 `composition == []`**（201 条 = 344 − 143），只有真正发生过的
  规则才有共现或 `["<singleton>"]` 标注；本次 `["<singleton>"]` 出现 0 次。

> 注意一个容易误读的点：**119 条负 witness 所属条目在 `traces_v2.json` 里同样被记为"命中该规则"**。
> 这不矛盾——traces 记的是"锚点行到达"，本次实测记的是"谓词真假"。同一位置在不同输入上
> 到达但为假，正是负 witness 要的信息。

---

## 4. 用 `rule_manifest.py --check` 预演（只报读数）

用候选清单 `fresh/gate_g4/manifest_proved_v1.json` + 同一 traces/jspace 外部执行：

```
python -X utf8 tools/completeness/rule_manifest.py --check \
  --universe …/gate_gap/universe_v2.json \
  --manifest fresh/gate_g4/manifest_proved_v1.json \
  --jspace  …/round9/judgment_space.json \
  --traces  …/gate_gap/traces_v2.json
```

| 预演字段 | 读数 |
|---|---|
| `total_rules` / `manifest_rules` | 344 / 344 |
| `unmapped_anchors` / `orphan_rules` / `anchor_orphans` | 0 / 0 / 0 |
| `proved` | **119** |
| `ready_proved` | **119** |
| `not_ready_proved` | **0** |
| `witness_errors` / `domain_errors` | 0 / 0 |
| `empty_cov` | **100**（不变） |
| `g4` / `reason` | **FAIL** / `mapping_or_proof_gap` |

- 工具内进程内预演与外部 CLI 预演**完全一致**（119 / 119 / 0 / 100 / FAIL）。
- **ready/total = 119/344**；`empty_cov = 100` 仍未消除，按 `rule_manifest.py` 的判据
  （`:190-195`）即使 344 条全部 proved，只要 `empty_cov != 0` 仍是 FAIL。
- 因此：**G4 未通过，本文件不宣称通过。**

若评审接受"弱负 witness"（见理论草案 4.4），proved 将是 **136**（+17），
`ready = 136`、`empty_cov` 仍 100、G4 仍 FAIL。该数字仅为敏感性参考，未写入候选清单。

---

## 5. 三个需要评审注意的结构性发现

### 5.1 `isinstance_ast` 家族（15 条）在 J 中零发生点

15 条 `isinstance_ast` 规则（`Assign`/`AsyncFunctionDef`/`Attribute`/`BoolOp`/`Call`/
`ClassDef`/`Compare`/`Constant`/`FunctionDef`/`If`/`List`/`Name`/`Set`/`Subscript`/`Tuple`）
全部 open，原因均为 `no_occurrence_in_J`：谓词在全部 36 个锚点上都能重建，但这 36 个锚点只落在

```
core/cfg/patch_detector.py (17)
core/cfg/objective_patch_detector.py (16)
core/cfg/patch_detector_enhanced.py (3)
```

——这些模块不在被执行的 pipeline（`build_cfg → RegionASTGenerator → CFGASTConverter →
CFGCodeGenerator`）路径上，因此 131 次运行中一次也没有执行到。**任何"以发生点为基础"的
定义都无法让它们 proved**；要做的是让 J 执行到这些模块（或显式决定把它们排除出分母）。

### 5.2 universe 快照已漂移：1209 / 5894 个锚点失效

| 项 | 数 |
|---|---|
| 声明锚点位置 | 5894 |
| 可重建谓词的位置 | 4685（+7 处同位置重复谓词 ⇒ 4692 个 candidate） |
| 已失效（位置存在但无该谓词） | **1209（20.5%）** |
| 源码里像谓词但未被 universe 声明的位置 | 1217（全部落在 2 个漂移文件内） |
| 完全失去锚点的规则 | 32 |
| 带失效锚点但仍能 proved 的规则 | 75 / 119 |

失效集中于两个文件：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`
（`universe_v2.json` 的 `files[]` 共登记 20 个源文件，其中 18 个的 `sha256` 与当前树一致，
这 2 个不一致）。
本次**不做锚点重定位**——重定位会改变"证明的是哪个锚点"，超出 v1 定义；因此 32 条规则记
`predicate_not_located`，`traces_v2.json` 在这两个文件上的行命中也不可全信：28 条规则出现
"traces 命中但实测零求值"（27 条因锚点漂移、1 条因该行未被实测执行）。

**建议**：先重建 universe 快照 → 重跑 traces → 再重跑本校验器，之后的 proved 数才具备
可比性。本文件所有数字是"漂移状态下的下限读数"。

### 5.3 行覆盖与谓词成立是两个量级不同的事

- 131 次运行里，累计 **13,521** 个 `(运行, 规则)` 组合被 traces 记为"命中"，但该次运行内
  该规则谓词**从未**为真（平均每次运行约 103 条规则）——`traces` 的 244 条 `rules_hit` 中，
  只有 143 条真正在 J 内产生过至少一次谓词匹配（`rules_with_measured_true = 143`）。
- 典型例子（均为 `opcode_eq`，位置热、谓词恒假）：`node.name == '<lambda>'` 求值 934 次全假、
  `optype == 'CALL_FUNCTION'`/`'JUMP_ABSOLUTE'`/`'DELETE_DEREF'` 等 3.11 下不存在的旧 opcode
  名、`node_type == 'Name'` 等。共 73 条。
- 因此 `traces_v2.json` 的 `rules_hit = 244` 应读作"**锚点行被到达的规则数**"，
  不能读作"规则被真正触发"。

---

## 6. 仍未覆盖（与"未 proved"分开读）

1. 100 条 empty_cov（含 15 条 `isinstance_ast`）：无发生点 ⇒ 本定义无话可说。
2. 规则语义正确性：谓词成立 ≠ 规则效果/意图正确；本定义明确不覆盖。
3. `composition` 的语义交互正确性：只记录"同一次归约里同时为真"，不判断交互。
4. J 之外输入域：不作断言。
5. 32 条漂移导致的"无法定位谓词"：属快照问题，非规则缺陷。

---

## 7. 复现

```powershell
# cwd = F:\Downloads\pythoncdc-main，解释器 D:/Python/python.exe（3.11.7）
$gap='.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/gate_gap'
$js ='.trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json'

D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py `
  --universe "$gap/universe_v2.json" --manifest "$gap/manifest_v2.json" `
  --jspace $js --traces "$gap/traces_v2.json" `
  --out fresh/gate_g4/proof_records_v1.json
# 同时写出 fresh/gate_g4/manifest_proved_v1.json（候选，未合并）

# 预演（只读导入 rule_manifest.check，工具内已自动做一次；也可单独跑）：
D:/Python/python.exe -X utf8 tools/completeness/rule_manifest.py --check `
  --universe "$gap/universe_v2.json" --manifest fresh/gate_g4/manifest_proved_v1.json `
  --jspace $js --traces "$gap/traces_v2.json"
```

产物：

| 文件 | 内容 |
|---|---|
| `fresh/gate_g4/G4_PROOF_THEORY.md` | v1 定义草案（本目录） |
| `fresh/gate_g4/proof_records_v1.json` | 344 条规则的逐条记录：`status / proof / witnesses / witness_evidence / composition / semantic_domain / reasons / measurement` |
| `fresh/gate_g4/manifest_proved_v1.json` | 由 `manifest_v2.json` 派生的候选清单（含 `v1_candidate` 标记，未合并） |
| `fresh/gate_g4/G4_V1_READINGS.md` | 本文件 |

---

## 8. 纪律自查

| 约束 | 状态 |
|---|---|
| 不改 `core/`、`scripts/`、`tests/` | ✅ `git diff --stat` 为空 |
| 不改 `rule_manifest.py`、`rule_universe.py`、`trace_g4_current.py` | ✅ `git diff --stat` 为空（仅只读 `import rule_manifest` 做预演） |
| 只新增校验器 + 定义草案 | ✅ 新增 `tools/completeness/rule_proof_check.py`、`fresh/gate_g4/*` |
| 不修改 `manifest_v2.json` | ✅ 只产出 `manifest_proved_v1.json` |
| 不用数字深度/计数上限 | ✅ 344 条规则全量、131 个 pyc 全量、无采样；早停仅在"已同时取得真/假见证"后停止重复求值 |
| 不用名字/常量/绝对偏移做谓词（I.4） | ✅ 谓词只由 universe 声明的 `kind+symbol` 在锚点处重建并对运行帧求值；`bytecode_offset`/`ast_path` 仅作 `occurrence_id` 身份 |
| 不宣称 G4 PASS | ✅ 预演读数 `ready=119/344`、`empty_cov=100`、`G4=FAIL` |
