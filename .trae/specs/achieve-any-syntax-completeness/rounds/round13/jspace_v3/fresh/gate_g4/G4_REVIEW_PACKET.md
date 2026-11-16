# G4 评审决策包（2026-11-17）

> 本文件不是"G4 已通过"，而是把 G4 剩余阻塞拆成**三个必须由评审裁决的问题**，每项附实测证据与
> 可选方案。裁决之前，G4 保持 **FAIL**，不写入任何 `proved` 到权威 manifest。

## 现状（谓词感知口径，可复算）

| 指标 | 值 | 来源 |
|---|---|---|
| universe | 344 规则 / 5896 occurrences | `fresh/gate_g4/universe_v3.json` |
| 谓词求值 | 1,920,617 次，为真 6,375（0.33%） | `G4_V3_READINGS.md` |
| `rules_hit_true` | 156 →（守卫口径修复后）211 | `traces_v3_guardfix.json` |
| `empty_cov_true` | 188 →（修复后）**133** | 同上 |
| proved | 127 →（修复后）**157** | `manifest_proved_guardfix_after.json` |
| 预演 `rule_manifest --check` | `empty_cov=133`、`ready 157/344`、**FAIL(mapping_or_proof_gap)** | 独立 CLI 复算 |

## 裁决一：36 条陈旧规则是否从宇宙排除

**证据**（`G4_EXCLUDE_DOSSIER.md`，36/36 逐条）：33 条 pattern 里的操作码名**不在
`dis.opmap`（CPython 3.11.7）**，另有 `CACHE`（`dis` 不产出的填充单元）与 2 个无生产者 IR 取值
（`GenExpr`、`__NESTED_FUNC__`）。这些规则**在任何 3.11 字节码上都不可能触发**。

**反证**：口径修复后这 36 条里有 23 条变"proved"，但全部 `symbol_observed=False`（只靠守卫求值为真，
被测符号从未出现）——这正是"规则陈旧"的证据，不是证明。

**方案**：
- A1 排除（推荐）：universe 344→308；需给 `rule_universe.py` 增加排除机制（**工具改动，需批准**），
  并在 manifest 里保留 `excluded_reason`。
- A2 保留：则这 36 条永远 `empty_cov`/`proved` 不可满足，G4 永不可能 PASS。

**若选 A1**：`empty_cov_true` 188（或修复后 133）中减去 36 → 仍需处理剩余 ~97 条。

## 裁决二：守卫口径与 `guard_only` 证明是否算 `proved`

**现象**（`G4_GUARDFIX_READINGS.md`）：把 membership 守卫统一为"集合整体求值"后，
**55 条由恒假转真**，其中 **31 条是陈旧规则**（23 条变 proved 但 `symbol_observed=False`，已单标
`guard_only`）；同时 **10 条原 proved 掉回 open**（`LOAD_NAME`/`LOAD_FAST`/`LOAD_GLOBAL`/
`STORE_FAST`/`STORE_DEREF` 等热守卫 131/131 恒真，`false_only=0`）。

**方案**：
- B1 保守（推荐）：`proved` 要求 `symbol_observed=True`；`guard_only` 只作诊断。这样 23 条不冒充证明，
  但 10 条掉回的仍缺负 witness ⇒ 计入裁决三。
- B2 宽松：接受 `guard_only` 为 proved ⇒ 读数好看（157→180 量级），但等于承认"守卫为真即规则成立"，
  与 v1 定义（"谓词在发生点成立"）不符，**不建议**。

## 裁决三：负 witness 的定义（54 条无严格反例）

**现象**：口径修复后"负 witness 缺失"从 29 升到 **54**。原因是这些规则对应的守卫/模式在**全部 131 个
运行里恒真**（如 `LOAD_FAST` 守卫 131/131 为真），按 v1 定义（"另一个 pyc 上到达同一锚点且谓词实测为
假"）**根本不存在**反例。

**方案**：
- C1 维持严格定义 ⇒ 这 54 条永远 open ⇒ **G4 不可能 PASS**。
- C2 放宽为"弱负 witness"：允许"谓词在同一锚点上不被求值/符号缺席"作为负 witness，需在
  `G4_PROOF_THEORY.md` 增补定义并评审；按上一轮敏感性参考，proved 会 +17 量级。
- C3 对"恒真守卫"类规则改判为 `tautology`（规则的 pattern 是恒真断言，无判别力）：这批规则本身应从
  宇宙排除或降级，需给出判定标准（例如：守卫在全部运行恒真且被测符号缺席 ⇒ 规则不可判别）。

## 裁决四（附）：44 条需补 J 的探针预算

`G4_J_BACKFILL.md`：44 条分 19 个形态组，覆盖全部最少 **18 条探针**；口径修复后 12 条已 proved、
4 条只需反例条目、28 条仍需正发生点 ⇒ **最少 16 条探针**。其中"类体级 `Return`"不可构造，建议改判
a 类（0 探针）。

## 结论（裁决前）

G4 在三种口径下的最好读数：**proved 134 / 分母 308**（读法 B：口径修复 + 排除 36）。即使四项裁决全部
按最宽松方向通过，仍需 16 条探针 + 54 条负 witness 的处置，才可能 `ready == total`。
**在这些裁决完成之前，G4 保持 FAIL，且不得以任何"预演 PASS"替代。**
