# G4 proof / composition 定义草案（v1，待评审）

- 文档状态：**DRAFT / 待评审**。当评审结论落地并写入 v2 之前，本文件定义的
  `proved` 不得被引用为 "G4 通过"、也不得被引用为 "规则已证明正确"。
- 实现：`tools/completeness/rule_proof_check.py`（`rule_proof_check/1.0.0`）
- 读数：`fresh/gate_g4/G4_V1_READINGS.md`
- 记录产物：`fresh/gate_g4/proof_records_v1.json`
- 候选清单：`fresh/gate_g4/manifest_proved_v1.json`（增量，**未合并**进 `manifest_v2.json`）

---

## 0. 一句话结论（存在语义的级别）

> **本定义证明的是「规则谓词在其被追踪的发生点上成立（pattern-match 见证）」，不是规则语义正确性的形式证明。**

它可以被准确复述为下面这条**单称存在命题**：

> 存在一个具体的 J 条目 `e⁺`（其 pyc 的一次区域归约运行）与其中一次具体的执行发生点
> `o`（锚点行被真实执行、谓词在该帧上被真实求值），使得规则 `r` 的谓词在 `o` 上求值为
> **真**，且存在另一个 J 条目 `e⁻` 与其中的发生点 `o'`，使得同一谓词在 `o'` 上求值为
> **假**。

它**不是**下面任何一条：

- 不是全称命题（没有对"所有输入/所有 pyc/所有帧"量化）；
- 不是形式化证明（没有机器检验的推导链、没有语义模型）；
- 不是规则语义正确性的证明（谓词成立与规则"效果正确/意图正确"无关）；
- 不是规则组合语义（composition）正确性的证明；
- 不是 G4 通过（G4 判据还要求 `empty_cov == 0` 且 `ready == total`，本次读数远未满足）。

级别命名建议（供评审统一口径）：**runtime pattern-match witness（实机模式匹配见证）**，
比 "tested-only" 强（因为负 witness 是被实测的否定点，不是随便挑的条目），
比 "proved（语义）" 弱（因为没有语义模型）。

---

## 1. 输入与口径

| 对象 | 文件 | sha256（本次） |
|---|---|---|
| 规则全集（分母） | `…/round13/jspace_v3/fresh/gate_gap/universe_v2.json` | `b80e7a26…ff42c` |
| 清单（映射/义务） | `…/gate_gap/manifest_v2.json` | `1ddfd476…b4057` |
| J（条目空间） | `…/attack-completeness-claims/rounds/round9/judgment_space.json` | `26130ade…75bc` |
| traces（行命中） | `…/gate_gap/traces_v2.json` | `32438040…d6dbe` |

两点必须写明：

1. `traces_v2.json` 自述其 `jspace` 指向 **round9** 的 `judgment_space.json`（1556 条、131 个
   distinct pyc）。因此 v1 的 J 就是它，witness 的合法性也以它为准（witness 必须 ∈ 该 J 的
   `entries[].id`）。`jspace_v3` 不是本次口径。
2. 规则粒度为 **`(kind, symbol)` 聚合规则**（`rule_universe.py` 的分组语义）：例如
   `opcode_eq / BINARY_OP` 是把所有 `opname == 'BINARY_OP'` 的锚点合成一条规则，它的
   "发生点"是这些锚点中任意一个被执行的时刻。`universe_v2.json` 共 344 条规则、
   5894 个声明锚点位置。

---

## 2. `proof` 的形式

### 2.1 定义

```
proof_id = sha256( rule_id | anchor | occurrence_id | predicate_kind |
                   observed_value | expected_value )
```

六个字段（UTF-8，`|` 分隔，参与哈希的原文同时写入 `proof.hash_input` 便于复核）：

| 字段 | 取值 | 含义 |
|---|---|---|
| `rule_id` | `RULE-xxxxxxxxxxxx` | universe 的规则 id（= `sha256(kind\|symbol)[:12]`，由 `rule_universe.py` 生成） |
| `anchor` | `file:line` | universe 的主锚点（`rule["anchor"]`，即该规则第一个声明锚点）。**实际发生位置**由 `occurrence_id` 里的 `file:line` 给出，它必然是这条规则 `anchors` 中的一个（校验器只会在声明锚点上重建谓词，绝不重定位到未声明的行） |
| `occurrence_id` | 见 2.2 | 具体发生点 |
| `predicate_kind` | `isinstance_ast` / `opcode_eq` | 谓词类型（本次口径只有这两类；`class_name_eq` / `region_type` 已在实现中支持但 universe 中为 0 条） |
| `observed_value` | `type=... value=...` | 发生点上被谓词约束的**运行时**值（实测取得；`repr` 超长时仅显示截断，截断只影响展示，不参与判定） |
| `expected_value` | `isinstance(ast.X)` / `== '<const>'` / `in <container>` | 谓词期望 |

### 2.2 `occurrence_id`

```
occurrence_id = entry_id | file:line | ast_path | code_object@bytecode_offset
```

- `entry_id`：J 条目 id（例 `JS-CONTINUE-010`），保证 witness 落在 J 内可复核；
- `file:line`：**声明锚点**所在文件与行（与 `anchor` 一致时说明证明用的就是这个声明位置；
  当规则有多个 anchors 时，取实际被实测到的那个声明锚点，并原样记录，不做改写）；
- `ast_path`：从 `Module` 到该谓词节点的结构化路径（例
  `Module.body[38].body[16].body[6].body[4].body[6].test`），用于在源码里唯一定位；
- `code_object@bytecode_offset`：执行该行的函数 `co_name` 与该次行事件的 `f_lasti`
  （块偏移），用于把"同一行多次执行"区分开。

> 纪律说明（I.4）：`bytecode_offset` 与 `ast_path` **只作身份标识**（identity），
> 从不参与谓词判定；谓词判定只依赖 universe 声明的 `kind` + `symbol` 与运行时帧值。
> 本定义也不使用任何"数字深度/计数上限"：344 条规则全部处理，131 个 pyc 全部运行，
> 每条规则的谓词在每个到达的发生点都参与求值（早停只用于"已经同时拿到真/假见证后
> 不再重复求值"，见第 5 节第 3 条，不影响任何见证的存在性判定）。

### 2.3 随 proof 一起记录的其他字段

```json
{
  "proof_id": "…64 hex…",
  "checker_version": "rule_proof_check/1.0.0",
  "definition_version": "G4 proof theory v1 (draft, pending review)",
  "definition_doc": "fresh/gate_g4/G4_PROOF_THEORY.md",
  "hash_input_format": "rule_id|anchor|occurrence_id|predicate_kind|observed_value|expected_value",
  "hash_input": "…参与哈希的原文…",
  "rule_id": "...", "anchor": "...", "occurrence_id": "...",
  "predicate_kind": "...", "observed_value": "...", "expected_value": "...",
  "review": null
}
```

`review` 始终为 `null`：v1 不自我批准。评审通过后由人写入评审记录，`proof_id` 不变。

---

## 3. `composition` 的定义（可观测）

### 3.1 定义

> `composition(r, e⁺) = { r' | 在与 `e⁺` **同一次区域归约运行**（同一 J 条目的 pyc，同一次
> pipeline 执行）中，`r'` 的谓词被本校验器**实测为真**至少一次 } \ { r }`

- 观测面：只在 **同一次 pipeline 执行**内共现（`build_cfg → RegionASTGenerator →
  CFGASTConverter → CFGCodeGenerator`），不是跨运行聚合；
- 判据：共现的成员必须是**实测为真**（`predicate_result == "true"`），即比 `traces_v2.json`
  的"锚点行到达"更严。`traces_v2.json` 的共现（行命中）作为对照存于 readings，
  但不进入 `composition`；
- 排序与去重：按 `rule_id` 字典序；不含自身。

### 3.2 它**不**声称什么

- 不声称两条规则**语义交互正确**（不声称它们在同一区域内交换/合并不产生冲突）；
- 不声称调度的先后、数据依赖或副作用顺序正确；
- 不声称该集合是最小充分集，也不声称集合稳定（它随 J 的 pyc 变化）；
- 集合大（本次 proved 规则的 `composition` 大小 10–79）只说明"同一次归约里同时为真的
  规则很多"，**不构成**任何交互正确性的证据。粒度仍是"一次 pipeline 执行"，
  未细化到 CFG region。

### 3.3 空集合的处理

分两种空，不得混淆：

**(a) 规则在该条目运行内为真、但没有任何其它规则同时为真**（本次 0 条）：

```json
"composition": ["<singleton>"],
"composition_meta": {"source": "measured_true_same_entry", "singleton": true, "cooccurring_rules": 0},
"notes": ["composition_singleton"]
```

**(b) 规则从未被实测为真**（无发生点 / 谓词恒假）：此时**没有发生点可谈共现**，`composition`
就是空数组，并写明理由，不给 singleton 标注（否则会把"没发生过"伪装成"发生过但独占"）：

```json
"composition": [],
"composition_meta": {"source": "measured_true_same_entry", "singleton": false,
                     "cooccurring_rules": 0,
                     "note": "empty: this rule was never measured true, so it has no occurrence to co-occur in"}
```

约束：

- `["<singleton>"]` 是一个**标注**，不是一条规则 id，评审可据此把它与真实共现区分；
- **不得伪造共现**：不允许回退到跨 pyc 聚合、不允许用 traces 的行共现冒充、不允许为了
  让 `composition` 非空而塞入任意规则；
- 本次读数：情形 (a) 0 条；情形 (b) 201 条（= 344 − 143 条曾实测为真的规则）
  `composition == []`，其余 24 条 open 规则（有正 witness、缺严格负 witness）保留了真实的
  实测共现。

`semantic_domain` 的 `hosts`/`depths` 与 `composition` 同源：取该规则**所有实测为真的
发生点**所属 J 条目的 `expected_label.host` / `expected_label.depth` 去重集合。

---

## 4. `negative witness` 的定义

### 4.1 定义（严格负 witness）

> `e⁻` 是 `r` 的负 witness，当且仅当：
> 1. `e⁻ ∈ J` 且 `e⁻ ≠ e⁺`，并且 `e⁻` 的 pyc 与 `e⁺` 的 pyc **不同**
>    （同一 pyc 的条目共享同一次执行，观测完全相同，不能充当"另一个条目"）；
> 2. `e⁻` 的运行**到达了同一锚点位置**（该谓词在 `e⁻` 上被真实求值过，至少一次）；
> 3. 在该次运行中，该谓词**每一次求值都为假**（即：`e⁻` 上规则不命中，尽管位置被到达）。

即负 witness 是"**位置到达 + 谓词实测为假**"的条目，而不是"随便挑一个没命中的 J 条目"。

### 4.2 选取优先级（可复核）

`同 form + 同 host` → `同 form` → `任意`，记录在
`witness_evidence.negative_selection ∈ {same_form_host, same_form, any}`；
form/host 取 `expected_label.form / expected_label.host`，缺失时回退到条目顶层字段。

### 4.3 为什么必须有"不同 pyc"这一条

`traces_v2.json` 的"命中"= 锚点行到达（coverage 行命中）。因此**任意**到达过锚点的条目
都会被 traces 记为"命中该规则"——如果允许用"同 pyc 的另一个条目"当负 witness，就会把
"同一次执行的不同 id"冒充成"另一个反例条目"。v1 明确排除这种情况。

### 4.4 弱负 witness（仅登记，不作 v1 判据）

若找不到严格负 witness，但存在另一个条目 `e⁻'`（不同 pyc）在该位置**至少一次**求值为假
（同时该条目也在别处为真），则记为：

```json
"witness_evidence": {
  "weak_negative": {…同一格式的 false 证据…},
  "weak_negative_witness": "JS-…",
  "weak_negative_selection": "same_form_host"
},
"notes": ["weak_negative_available"]
```

它**不**计入 `witnesses.negative`、**不**改变 `status`。是否接受为 v2 判据，是评审决定项
（接受后本次 proved 从 119 → 136，见 readings）。

### 4.5 本次读数

- 严格负 witness：119 条（`same_form_host` 77 / `same_form` 24 / `any` 18）；
- 缺严格负 witness：24 条（其中 17 条有弱负 witness，7 条两者皆无；7 条中最极端的一条
  `false_evals == 0`，即"位置一到即真"，在 J 内不存在任何否定点）。

---

## 5. 实现如何做到"实测"（可复现）

1. **谓词重建**（静态，只读）：对 universe 里每个声明锚点 `(file,line,kind,symbol)`，
   按 `rule_universe.py` 的扫描形状在源码里重建谓词表达式：
   - `isinstance_ast / X` → `isinstance(<subject>, ast.X)`（对 tuple 形式按 **每个 symbol**
     分别重建，避免"匹配到兄弟类型也算真"的假阴性/假阳性）；
   - `opcode_eq / '<const>'` → `left == '<const>'`（`in (…)` 常量容器按每常量重建）；
   - `opcode_eq / <container>` → 原样的 `left in <container>`。
   重建失败（源已漂移、位置无谓词）→ 该锚点记为不可定位，规则记 `predicate_not_located`。
   **交叉验证**：universe 登记的 20 个源文件中 18 个未漂移，其中 14 个承载锚点；在这 14 个
   锚点文件上"重建谓词集合"与 universe 声明**完全一致**（0 个未映射、0 个缺失；1209 个缺失
   与 1217 个未声明谓词全部落在另外 2 个漂移文件内），说明重建忠实于扫描器语义。
2. **运行与求值**（动态）：对 J 的每个 distinct pyc 跑一次区域归约 pipeline，用
   `sys.settrace` 只在"该 code object 含有声明锚点行"的帧上开行级追踪；行事件命中声明
   锚点时，用该帧的 `f_globals/f_locals` 对重建的谓词 `eval`，得到 `predicate_result`，
   并单独求值谓词的 subject 得到 `observed_value`。
3. **早停**：仅当某规则在**本次运行**内已经同时取得真与假时，本次运行内不再重复求值该
   规则（不改变真/假见证的存在性，也不改变"本次运行内是否出现过真"的结论）。
4. 全程不修改 `core/`、`scripts/`、`tests/`、`rule_manifest.py`、`rule_universe.py`、
   `trace_g4_current.py`；只读导入 `rule_manifest.check` 做预演。

已知实现边界（须与语义边界区分）：

- 单进程追踪：pipeline 若在子线程中执行，子线程不会被子线程外的 `sys.settrace` 覆盖；
  本次 131 次运行 `run_failures` 为空、且"实测为真但 traces 未记"的规则数为 0，
  未观察到该问题，但 v2 应以 `threading.settrace` 兜底；
- `observed_value` 的 `repr` 截断仅影响展示。

---

## 6. 本定义**不能**覆盖的范围（必须与"未 proved"分开读）

1. **无发生点的规则（empty_cov）**：`traces_v2.json` 口径下 100 条规则的锚点行在任何 J
   条目中都不被执行；本校验器实测为"零次求值"的规则 128 条 = 这 100 条 ∪ 27 条
   "有行命中但锚点已漂移、谓词无法重建"的规则 ∪ 1 条"有行命中但该行在实测中从未被执行"
   的规则（100 条内部还含 5 条同时"不可定位"）。
   - 其中**全部 15 条 `isinstance_ast` 规则**的锚点只落在
     `core/cfg/patch_detector.py`(17)、`objective_patch_detector.py`(16)、
     `patch_detector_enhanced.py`(3)，这些模块不在被执行的 pipeline 路径上
     ⇒ 在任何"以发生点为基础"的定义下都**不可能** proved。
   - D1/D2/D3 那 100 条 empty_cov 规则属于同一类：**没有发生点 ⇒ 没有 witness ⇒
     本定义无法表态**。要让它们可证，需要的是"让 J 真的执行到那些分支"（或显式把
     它们从 G4 分母中排除），而不是放宽 proof 定义。
2. **规则语义正确性本身**：谓词在实测点成立，不代表该分支产生的 AST/字节码/区域划分
   在语义上是正确的。要覆盖它需要另一套判据（差分语义、可执行等价性、编译-反编译往返
   不变式），不在本定义内，也不应由本校验器冒充。
3. **composition 的语义交互正确性**（见 3.2）。
4. **J 之外的输入域**：本定义只对 J（1556 条、131 个 pyc）内的发生点成立；对未进入 J 的
   输入不作任何断言。
5. **源漂移下的锚点**：2 个文件（`core/cfg/region_analyzer.py`、`region_ast_generator.py`）
   的 `source_sha256` 与当前树不一致，5894 个声明锚点中 1209 个（20.5%）已不能重建谓词，
   32 条规则因此完全没有可定位锚点。这是 universe 快照问题，**不是**规则缺陷；v1 对它们
   记 `open`（`predicate_not_located` + `anchor_source_drift`），不做重定位——因为重定位
   会改变"证明的是哪个锚点"，属于超出本定义的动作。

---

## 7. 与现有 G4 判据的对应关系

`rule_manifest.py --check`（:157-195）要求 `status=="proved"` 的规则同时满足 4 项，
本 v1 定义逐项给出可复核来源：

| G4 判据 | v1 提供 | 本次是否满足 |
|---|---|---|
| (a) `witnesses.positive` + `witnesses.negative`，且都在 J 里 | 正向 = 实测为真的发生点条目；负向 = 4.1 的严格负 witness；ids 直接来自 J | 119 条同时具备，且 ids 全在 J 内（见 readings 的自洽审计） |
| (b) `semantic_domain.hosts` + `depths` | 该规则所有"实测为真"发生点所属条目的 `expected_label` 去重 | 119 条均非空（hosts 3–48 个、depths 1–3 个） |
| (c) `proof.proof_id` 非空 | 2.1 的 sha256，含 `checker_version` | 119 条非空且可重算 |
| (d) `composition` 非空 | 3.1 的实测共现；规则发生过但无共现则 `["<singleton>"]` 标注；从未发生过则空数组 | 119 条非空（10–79 条规则；singleton 0 条） |
| `empty_cov == 0` | **不提供**，也无法提供 | ✗（仍为 100） |
| `ready == total` | — | ✗（119/344） |

**结论表述纪律**：`manifest_proved_v1.json` 只是候选增量文件；`manifest_v2.json` 未被改动；
G4 **未通过**，且本次不宣称通过。预演读数见 `G4_V1_READINGS.md` 第 4 节。

---

## 8. 评审清单（决定 v1 → v2）

1. **是否接受"行到达 ≠ 谓词成立"这一区分**并把它作为 G4 的新基础。本次实测显示差别很大：
   244 条被 traces 记为"命中"的规则里，73 条在其锚点上**从未**求值为真；119 条 proved 的
   负 witness 条目在 traces 里同样被标为"命中"。
2. **是否接受弱负 witness**（4.4）。接受则 proved 119 → 136；不接受则保留 24 条 open。
3. **是否接受 `composition` 的粒度**（"一次 pipeline 执行"）与规模（10–79）。若要求
   "同一区域归约步骤内"更细，需要 CFG region 级别的分段标记（属于 pipeline 侧改动，
   本工具不擅自引入）。
4. **是否要求先重建 universe 快照**（2 个漂移文件）再采信任何 proved 数。
   本 v1 的数字是在漂移状态下取得的保守下限所对应的读数（75/119 条 proved 规则还带有
   不可定位的锚点）。
5. **empty_cov 的处置**：100 条无发生点规则（含全部 15 条 `isinstance_ast`）要么让 J 执行
   到那些模块/分支，要么显式决定把它们排除在 G4 分母之外。这必须是一个**显式评审决定**，
   不能由校验器自行"放宽"。

---

## 9. 名词速查

| 词 | 本文件中的确定含义 |
|---|---|
| 发生点 / occurrence | 某 J 条目运行中，某声明锚点行被执行、且该谓词在该帧上被求值的那一次事件 |
| 实测为真 | 校验器在该帧 `eval` 谓词得到 `True`，并记录了 `observed_value` |
| 行命中 / trace hit | `traces_v2.json` 中"锚点行被执行"，**不含**谓词真假信息 |
| 谓词 | universe 声明的 `(kind, symbol)` 对应的可判定表达式，由源码在锚点处重建 |
| 严格负 witness | 4.1 三条全满足的条目 |
| 弱负 witness | 4.4 的条目，仅登记 |
| singleton composition | `["<singleton>"]` 标注，表示本次运行内无实测共现 |
