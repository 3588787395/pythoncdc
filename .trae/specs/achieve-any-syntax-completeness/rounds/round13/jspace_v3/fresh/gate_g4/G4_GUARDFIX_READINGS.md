# G4 校验器口径修复实测读数（1.0.0 → 1.1.0）

**状态：预演读数，需评审。** 未改 universe / manifest / J / traces 输入，未把任何 status 写进权威 manifest。

本轮只改 `tools/completeness/rule_proof_check.py`（D1 membership 守卫求值口径、D2 kind 记账）；`rule_universe.py`、`rule_manifest.py`、`core/`、`scripts/`、`tests/` 未改动。候选重建 5909 条、`unmapped=0`（与修复前一致）。输入未被写回：universe/manifest/jspace 的 sha256 在 before/after 两次运行中一致（`identical_before_vs_after=True`）。

## 1. proved / open

| 项 | 修复前 | **修复后** | 变化 |
|---|---|---|---|
| proved | 127 | **157** | +30 |
| open | 217 | **187** | -30 |
| open 原因 `negative_witness_missing` | 29 | **54** | +25 |
| open 原因 `no_occurrence_in_J` | 100 | **100** | +0 |
| open 原因 `predicate_false_at_site` | 88 | **33** | -55 |
| 至少真过一次（= 344 − empty_cov_true） | 156 | **211** | +55 |
| `empty_cov_true`（traces 口径，重录后） | 188 | **133** | -55 |
| 预演 `rule_manifest --check` 的 empty_cov | 188（traces_v3） | **133**（重录 traces） | -55 |

`empty_cov_true` 必须用**重录**的 traces 比较：`traces_v3.json` 是修复前口径录的；本轮另录 `traces_v3_guardfix.json`，`rules_hit_true=211`、`empty_cov_true=133`，与 `proof_records_guardfix_after.json` 的 `rules_with_measured_true=211` 自洽（`matches_proof_records=True`）。

## 2. 任务一·1：membership 守卫统一口径（D1）

修复位置：`_guard_tests()` / `_scan_file()` / `Measurer._evaluate()`。**同一构造只保留一套口径**：所有 membership 守卫（字面量元组、命名集合）一律按整条守卫求值（`observed in {members}`），不再投影成 `observed == 'X'`；单成员投影降级为**诊断量** `member_projection`（只在守卫为真时测），永不参与 status。

### 2.1 8 条 c 类逐条实测

| rule_id | symbol | 修复前真 | **修复后真** | 守卫成员 | 投影真 | 到达运行 | 为真/仅假 | status |
|---|---|---|---|---|---|---|---|---|
| `RULE-1c5bd7459d99` | `POP_JUMP_BACKWARD_IF_NOT_NONE` | 0 | **52** | 2 | 0 | 131 | 52/79 | `proved` |
| `RULE-38d1a1fef6a0` | `DELETE_DEREF` | 0 | **3** | 2 | 0 | 131 | 3/128 | `proved` |
| `RULE-639e08245c2d` | `POP_JUMP_BACKWARD_IF_NONE` | 0 | **49** | 2 | 0 | 131 | 49/82 | `proved` |
| `RULE-6cc7b6a37fd5` | `SET_ADD` | 0 | **9** | 5 | 0 | 9 | 9/0 | `open` |
| `RULE-8a6101820c9d` | `DELETE_GLOBAL` | 0 | **7** | 12 | 0 | 131 | 7/124 | `proved` |
| `RULE-b620fe7fb512` | `LOAD_CLASSDEREF` | 0 | **132** | 6 | 0 | 131 | 131/0 | `open` |
| `RULE-ec53116b4211` | `List` | 0 | **2** | 2 | 0 | 1 | 1/0 | `open` |
| `RULE-efc4bb08d567` | `DELETE_NAME` | 0 | **7** | 2 | 0 | 131 | 7/124 | `proved` |

**8/8 全部由「谓词恒假」变为「谓词为真」；5 条 proved，3 条转 open（原因改为 `negative_witness_missing`）。** 3 条未 proved 的原因不是口径没修好，而是它们的守卫在**每一次**到达站点的运行里都为真（`SET_ADD` 9/9 运行、false_only=0；`LOAD_CLASSDEREF` 131/131 运行、false_only=0；`List` 1/1 运行、false_only=0），于是「另一条 J 让谓词为假」的严格负 witness 在现有 1556 个 J 条目 / 131 个 pyc 运行里不存在。要救这 3 条只能补**守卫不成立的反例条目**，不能放宽负 witness 判据。

### 2.2 连带效应（必须一起评审）

- 谓词由假转真的规则共 **55** 条：a 类 31、c 类 8、d 类 16。
- a 类 31 条（23 proved / 8 open）：**本来就该排除**（见 `G4_EXCLUDE_DOSSIER.md`）。guard 级真值由同守卫的**活兄弟成员**满足，本名字 `symbol_observed` 仍为 `False`；这类 proved 校验器单独标 `guard_only=true`（全库 43 条，其中 a 类 23 条）。
- **10 条原本 proved 的规则掉回 open**：`RULE-196b1a690257`(LOAD_NAME) 131/131、false_only=0；`RULE-1e003061d4c8`(LOAD_DEREF) 131/131、false_only=0；`RULE-440f9734bda7`(LOAD_FAST) 131/131、false_only=0；`RULE-4f50e56b6e25`(STORE_FAST) 131/131、false_only=0；`RULE-5949b5021f68`(STORE_DEREF) 131/131、false_only=0；`RULE-5f8a4ca1dd8a`(LOAD_GLOBAL) 131/131、false_only=0；`RULE-6997aa6c7097`(STORE_SUBSCR) 131/131、false_only=0；`RULE-6b8f5b50d608`(LOAD_CLOSURE) 131/131、false_only=0；`RULE-db3c378f2dad`(STORE_ATTR) 131/131、false_only=0；`RULE-e77fbe9ddbee`(STORE_GLOBAL) 131/131、false_only=0。原因统一：守卫在每次到达运行里都为真（false_only=0），改用守卫口径后找不到「谓词为假」的条目 ⇒ `negative_witness_missing`。这是 guard 口径的**真实代价**，不是实现错误。
- 结论：**统一口径不能单独上线**，必须与 (a) 36 条 a 类排除、(b) `symbol_observed` 标记一起评审；否则 proved 从 127 涨到 157，其中 23 条是死名字的空证明。

### 2.3 两种读法

| 读法 | 分母 | proved | open | 从未为真 |
|---|---|---|---|---|
| A 只修口径（universe 不变） | 344 | **157** | 187 | 133 |
| B 修口径 + 排除 36 条 a 类（候选，未施加） | 308 | **134** | 174 | 128 |

B 的 +7（127→134）= c 类 +5、d 类 +12、再减 10 条守卫恒真造成的降级。

## 3. 任务一·2：kind 记账（D2）

`OP_NAMES` 拆成 `OPCODE_NAMES={opname,opcode}` 与 `IR_MARKER_NAMES={name,kind,node_type,node_name}`；每条记录新增 `pattern_class`（按重建谓词判定）与 `universe_kind`（可追溯），候选新增 `ast_marker_eq` / `ast_marker_in_set` / `ast_marker_in_named_set`。

### 3.1 anchor 级 kind 分布（344 条，按其声明 anchor 上的谓词形态）

| anchor pattern_class | 规则数 | 其中属于 88 条 D3 | 修复前 proved | 修复后 proved |
|---|---|---|---|---|
| `ast_marker_eq` | 50 | 25 | 5 | 14 |
| `ast_marker_in_set` | 14 | 1 | 1 | 1 |
| `isinstance_ast` | 15 | 0 | 0 | 0 |
| `opcode_eq` | 78 | 12 | 63 | 66 |
| `opcode_in_named_set` | 94 | 11 | 36 | 36 |
| `opcode_in_set` | 93 | 39 | 22 | 40 |

88 条 D3 里 anchor 形态为 AST 标记的有 **26** 条 —— 正是定性报告说的 26 条（修复前全部被记进 `opcode_eq`）。修复后 `proved_by_pattern_class={"ast_marker_eq": 3, "mixed:ast_marker_eq,ast_marker_in_set": 12, "mixed:opcode_eq,opcode_in_set": 73, "opcode_eq": 5, "opcode_in_named_set": 36, "opcode_in_set": 28}`。

## 4. 复现

```powershell
# 修复前基线（未改校验器；逐字复现 127/217、empty_cov 188）
D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py \
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_v3.json \
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --traces  fresh/gate_g4/traces_v3.json \
  --out fresh/gate_g4/proof_records_guardfix_before.json \
  --manifest-out fresh/gate_g4/manifest_proved_guardfix_before.json
# 修复后（同输入）
D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py \
  --universe fresh/gate_g4/universe_v3.json --manifest fresh/gate_g4/manifest_v3.json \
  --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --traces  fresh/gate_g4/traces_v3.json \
  --out fresh/gate_g4/proof_records_guardfix_after.json \
  --manifest-out fresh/gate_g4/manifest_proved_guardfix_after.json
# 重录谓词口径 traces，再跑一次（自洽读数）
D:/Python/python.exe -X utf8 fresh/gate_g4/trace_g4_v3.py --universe fresh/gate_g4/universe_v3.json \
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
  --out fresh/gate_g4/traces_v3_guardfix.json
D:/Python/python.exe -X utf8 tools/completeness/rule_proof_check.py ... --traces fresh/gate_g4/traces_v3_guardfix.json \
  --out fresh/gate_g4/proof_records_guardfix_after_consistent.json
```
