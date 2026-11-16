# G3 三段式判定 · 6 条残余定性 · 覆盖分子修正（G3_DECISIONS）

日期：2026-11-17　基线提交：`d22ebd6c`　复跑判据 sha256：`d31948b3a0a4336078d3e031467fa942947c358ecc7584c5194bd389d1a9cc38`
改动文件：**只有** `tools/completeness/mutation_test.py`（1.0.0→1.1.0）与
`tools/completeness/coverage_checker.py`（2.0.0→2.1.0）。
未改 `scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/`、`core/`、
`TOLERANCE_REGISTRY.md`、`semantic_diff.py`；R7 阻断强度未放宽。

---

## 0. 结论摘要

| # | 事项 | 结果 |
|---|---|---|
| 1 | 三段式判定 | 已实现（`classify()`）；三方向自测 3/3 + 生成器/一致性各 1 项，**6/6 通过** |
| 2 | 30 案新读数（三段式 + 生成器修正 + 4 条 proof） | **KILLED 628 / EQUIVALENT 4 / MISSED 0 / FALSE_KILL 0 / ERROR 1**（evaluated 633） |
| 3 | 6 条残余定性 | 2 条 = 语义 no-op（源码逐字节**不同**，编译 code object 全同）→ 生成器修正；4 条 = 顶层 `co_code` 等价改写（固定常量下 boolop 短路形）→ proof 归 EQUIVALENT；**0 条真差异留在 missed** |
| 4 | J 空间覆盖分子 | `covered_5tuple` **1180 → 1151**，`green` **1151**，`r7_only_different` **29**（=转出条目数），`semantic_failures` 29 |
| 5 | G2b（402，冻结产品重判） | 395 条产品哈希完好子集：EQUAL 57 / DIFF 1 / ERROR 337 **不变**；**转 DIFF 0**；7 条产品已漂移（0354/0373 旧 DIFF→EQUAL） |
| 6 | G2c（46，冻结产品重判） | 24 DIFF / 5 EQUAL / 17 ERROR → **26 DIFF / 3 EQUAL / 17 ERROR**；**转 DIFF 2**（REAL46-002、REAL46-024，均 R7-only 嵌套 `co_code`） |

---

## 1. 任务一：`mutation_test` 三段式

### 1.1 实现点

| 位置 | 内容 |
|---|---|
| `mutation_test.py:341` `classify(semantic_status, proof, diffs)` | 唯一判定入口，四分支见 1.2 |
| `mutation_test.py:324` `_r7_only(diffs)` | `diffs` 非空且每条 `dimension == "R7"` 才为真（R7-only 证据） |
| `mutation_test.py:437`（run_mutations 内） | 每条 mutant 调 `classify(...)`；`equivalence_note` 区分「R7-only + proof」与「proof 但非 R7」 |
| `mutation_test.py:119` `generate_mutations(..., skip_identity=True, skipped=None)` | 生成阶段剔除 no-op：候选编译后的 code object 与基线**全等**即不是 mutant（不分配 `mutation_id`） |
| `mutation_test.py:265` `_code_identity()` / `:280` `_compiled_identity()` | code object 同一性比较（`co_code/co_consts/co_names/co_varnames/…/co_exceptiontable/co_qualname`；不含已登记可忽略的 `co_filename/co_firstlineno/co_linetable`） |
| `mutation_test.py:396` `report["generator_fixes"]` | 被剔除的候选逐条入档（`reason="identity_no_op"`、`text_identical`、`note`），summary 加 `identity_skipped` / `generated_raw` |
| CLI | 新增 `--keep-identity`（复现旧读数）与 `--selftest`（三方向自测）；`--case` 在有 `--selftest` 时不再强制 |

### 1.2 判定规则（替换旧两段式）

```text
semantic == DIFFERENT:
    无 proof                        -> KILLED          # R7 阻断：code object 差异是 kill 证据，不是 survivor
    有 proof 且 diffs 全是 R7       -> EQUIVALENT      # 嵌套 co_code / 常量拼写 / 未调用函数体
    有 proof 且含非 R7（R0–R6/LOAD）-> FALSE_KILL      # proof 不能为行为级证据背书
semantic == EQUAL:
    有 proof -> EQUIVALENT ; 无 proof -> MISSED
semantic == INCONCLUSIVE -> INCONCLUSIVE ; ERROR -> ERROR
```

与旧实现的差异（这是本轮读数变化的全部来源）：

| 情形 | 旧 | 新 |
|---|---|---|
| DIFFERENT + 顶层 code metadata-only + 无 proof | MISSED | **KILLED** |
| DIFFERENT + 嵌套 code 真实差异 + 有 proof | FALSE_KILL | **EQUIVALENT**（若 R7-only） |
| DIFFERENT + 非 R7（R1–R6）+ 有 proof | FALSE_KILL | FALSE_KILL（**唯一保留**的 FALSE_KILL 情形） |
| EQUAL + 无 proof | MISSED | MISSED（现只由生成器漏网时出现） |

`_code_metadata_only()` 保留为**诊断辅助**（G3 探针仍在用），判定不再依赖它。

### 1.3 三方向自测（`mutation_test.py --selftest`，exit 0）

```text
direction1_proof_r7_only_different_is_equivalent   true    # f(x)=x*1, Mult->FloorDiv, 有 proof；DIFFERENT(R7) -> EQUIVALENT
direction2_no_proof_different_is_killed            true    # 同一变异，无 proof；DIFFERENT -> KILLED
direction3_proof_plus_non_r7_is_false_kill         true    # f(a,b)=a-b, Sub->Add, 故意错误 proof；R1+R7 -> FALSE_KILL
generator_drops_identity_mutant                    true    # f(): return None -> return；text_identical=False，编译产物同 -> 生成期剔除
identity_mutant_would_be_missed                    true    # 强制 --keep-identity 时同一候选 = EQUAL -> MISSED
no_different_mutant_is_missed                      true    # 任何 DIFFERENT 都不可能被写成 MISSED
passed true   (6/6)
```

日志：`D:/temp/opencode/cl_layout/gap/g3gap/selftest_mutation_final.json`。

### 1.4 回归（如实登记 1 项既有冲突）

`tools/completeness/mutation_test_selftest.py`（**未改，按纪律只改两个工具**）9 项检查 **8 通过 1 失败**：

```text
失败项：code_only_unproven_missed = false
        该断言要求「metadata-only DIFFERENT + 无 proof ⇒ MISSED」——正是被本任务规范取代的旧两段式语义；
        其余 8 项（baseline_equal/complete/has_kills/has_missed/no_false_kill/equivalent_*）全 True。
```

该测试文件的这条断言已过期；本轮只允许修改上述两个工具文件，故未擅自改它，
新的权威自测是工具内置 `--selftest`（6/6）。日志：`g3gap_legacy_mut_selftest.json`。

---

## 2. 任务二：30 案复跑与 6 条残余定性

### 2.1 复跑口径

```text
python -I -X utf8 tools/completeness/mutation_test.py \
  --case .trae/specs/attack-completeness-claims/rounds/round9/g3_mutation/case_<ID>.json \
  --source <case.product.source 的绝对路径> --max-mutants 25 --out ...
```

30 案 × 25 条上限（与 `G3_RULER_FIX.md` 同口径）。驱动脚本 `_g3_run30.py`（本目录）。

| 配置 | KILLED | EQUIVALENT | MISSED | FALSE_KILL | ERROR | evaluated | identity_skipped |
|---|---:|---:|---:|---:|---:|---:|---:|
| 旧两段式（`d22ebd6c` 后，`G3_RULER_FIX` 读数） | 628 | 0 | 6 | 0 | 1 | 635 | — |
| **新三段式 + 生成器修正，无 proof** | **632** | 0 | **0** | 0 | 1 | 633 | 2 |
| **新三段式 + 生成器修正 + 4 条 proof（终态）** | **628** | **4** | **0** | 0 | 1 | 633 | 2 |

生成器修正在 JS-BREAK-001 / JS-WHILE-040 各剔除 1 条（`gen 15→14`，被剔除者原是 M0014，位于末位，
因此其余 28 案的 `mutation_id` 编号零位移，可与旧报告逐条对齐）。终态合并读数见
`run30_final.json`（= 默认 30 案 + RETURN-033/070 的 4 条 proof：KILLED 628 / EQUIVALENT 4 / MISSED 0 /
FALSE_KILL 0 / ERROR 1 / evaluated 633）。

### 2.2 6 条逐条定性

#### (a) 2 条 identity no-op：JS-BREAK-001 M0014 · JS-WHILE-040 M0014

| 项 | 实测 |
|---|---|
| 变异 | `return` 算子：`return <value> -> return None`，行 19/20，路径 `body[1].body[4].body[3]` |
| 变异源码 vs 基线源码 | **逐字节不同**：基线该行为 `        return None`，变异为 `        return`（全文件仅此 1 行不同；sha256 不同） |
| 变异源码 vs 基线 code object | **全等**（`_code_identity` 相等：模块 `co_code` 36 字节逐字节相同，`co_consts` 递归结构相同，`co_names/co_varnames/co_flags/co_stacksize` 相同） |
| judge 判定 | `EQUAL`（diffs=[]；R1–R7 全部无差异） |
| 旧状态 | MISSED（EQUAL + 无 proof） |
| 定性 | **语义 no-op，不是 survivor**。`return None` 与裸 `return` 在 CPython 3.11 编译为同一段 `LOAD_CONST None; RETURN_VALUE`，任何观测维度都无法区分。 |
| 处置 | **生成器修正**：在三段式之外，`generate_mutations()` 生成期按「编译产物 code object 与基线全等」剔除，report 记 `generator_fixes[].reason="identity_no_op"`，不进 mutant 分母。`--keep-identity` 可复现旧读数（MISSED=1/案）。 |

**与任务预设的差异（必须如实指出）**：任务书写的是「核对变异源码与基线源码是否逐字节相同；若相同 ⇒
生成器缺陷」。实测**不是**逐字节相同（`return None` → `return`），但**编译产物是同一个 code object**，
因此判据落在「语义 no-op」而不是「文本相同」。若只按文本判等，这两条永远不会被识别为 no-op。
（注：`identity_dossier.json` 里的 `co_consts_equal=false` 是 Python `==` 对嵌套 code object 按对象同一性
比较造成的假差；结构比较 `_code_identity` 为全等，judge 的零 diff 亦证实无差异。）

#### (b) 4 条顶层 `co_code`：JS-RETURN-033/070 的 M0006、M0008

两案指向**同一源文件** `test_repros/round3/e02_g1_b98_hosts.py`（模块级 `_P,_Q,_R,_S = (1,2,3,4)`，
`M1 = (_P or _Q) and _R`、`M2 = _P or (_Q and _R)`），因此 4 条 = 2 个变异 × 2 个 J 条目。

| case / mutant | 变异 | 唯一差异（模块 code object） | 长度/常量/名字 | judge | 终态 |
|---|---|---|---|---|---|
| JS-RETURN-033 M0006 | `M1` 里 `or`→`and` | 偏移 **18**：`POP_JUMP_FORWARD_IF_TRUE 2 (to 24)` → `JUMP_IF_FALSE_OR_POP 3 (to 26)`；偏移 24 的 `LOAD_NAME _R` 不再是跳转目标 | `co_code` 112→112 字节；`co_consts/co_names/co_stacksize` 全等 | DIFFERENT（R7×1） | **EQUIVALENT**（proof） |
| JS-RETURN-033 M0008 | `M2` 里 `and`→`or` | 偏移 **34**：`JUMP_IF_FALSE_OR_POP 1 (to 38)` → `JUMP_IF_TRUE_OR_POP 1 (to 38)`（目标不变） | 112→112；常量/名字全等 | DIFFERENT（R7×1） | **EQUIVALENT**（proof） |
| JS-RETURN-070 M0006 | 同上 M0006 | 同上（同源文件） | 同上 | DIFFERENT（R7×1） | **EQUIVALENT**（proof） |
| JS-RETURN-070 M0008 | 同上 M0008 | 同上 | 同上 | DIFFERENT（R7×1） | **EQUIVALENT**（proof） |

- **只是偏移/常量索引吗？** 不是纯偏移：M0006 换了 opcode 且把 24 的落点吸收进 26 的短路链；
  M0008 只换 opcode（`IF_FALSE_OR_POP`→`IF_TRUE_OR_POP`），偏移与目标都不变。两者都不是「偏移/常量索引漂移」，
  而是**两个语义等价的短路形状**。
- **为什么不改可观测行为**：模块级绑定固定为 `_P,_Q,_R = 1,2,3`。基线 `(1 or 2) and 3 = 3`，
  变异 `(1 and 2) and 3 = 3`；基线 `1 or (2 and 3) = 1`，变异 `1 or (2 or 3) = 1`。两侧只有
  `LOAD_NAME`/短路跳转/`STORE_NAME`，无调用、无属性访问、无容器写入；差异最多是「多读一次名字」，
  读名字本身无可观测副作用。R1（模块值 M1/M2）、R2/R3（无输出）、R4（无事件）、R5（module_values/aliases）、
  R6（无异常）测量结果逐项相同——这一点由 judge 的 `diffs` 只有 R7 直接佐证，proof 只补「为何 R7 差异
  不影响可观测行为」的论证，**不是**把真差异写成等价。
- proof 文件：`fresh/gate_gap/equivalents_g3_topcodec.json`（proof 文本含具体指令、偏移、常量取值与求值结果）。
- 终态：4 条 EQUIVALENT、KILLED 628、ERROR 1、MISSED 0、FALSE_KILL 0。

#### (c) 1 条 ERROR（非 missed，原样保留）

JS-AUGFORM-031 M0005（`Mult -> FloorDiv`，行 10）：`semantic_status=ERROR`、
`errors=["product worker/harness error"]`（产物侧 worker 加载/执行失败，非反编译判定）。
修复前后同为 ERROR，**未计入 killed、未计入 missed**，也未用 proof 掩盖。

#### (d) 判定结论

- 6 条里 **2 条是生成器缺陷**（真 no-op，按生成期剔除处理，报告记「生成器修正」）；
  **4 条是行为等价的顶层字节码改写**（有 proof，归 EQUIVALENT）。
- **没有一条真差异被写成等价**：4 条的等价性独立于 mutation 分数（R1–R6 全等在 judge 侧已成立），
  且 `FALSE_KILL` 分支现在专门拦截「proof 与行为级证据冲突」的情况（自测方向 3 实测通过）。

---

## 3. 任务三：`coverage_checker` 分子修正

### 3.1 旧判据确认

旧 `check()`：只要 C1–C5 齐全即 `covered_5tuple`，**`DIFFERENT` 也计入**（`green` 额外要求 `verdict==EQUAL`）。
所以修尺子后 `green` 1180→1151、而 `covered_5tuple` 停在 1180——分子把 R7-different 也算成 covered。

### 3.2 新判据（只收紧分子，不动其他维度）

| 位置 | 内容 |
|---|---|
| `coverage_checker.py:233` `_r7_only_different(verdict, c4)` | `verdict=="DIFFERENT"` 且 `c4.diffs` 为**非空列表**且每条（去空白后）严格等于 `R7` |
| `coverage_checker.py:285` | 在 C1–C5 **全部通过之后**再判：R7-only DIFFERENT → 新状态 `r7_only_different`（reason `c4_r7_only_different`），**不进 `covered_5tuple`** |
| 未放宽 | C1–C5 五条判据逐字未动；`diffs` 缺失/为空、`DIFFERENT` 含任一非 R7 维度、`EQUAL/INCONCLUSIVE/ERROR` 全部按原规则处理 |
| 产物 | `totals.r7_only_different`、`per_family[*].r7_only_different`、`payload.r7_only_different`（条目清单）、MD 报告新增一列与口径段 |

### 3.3 新读数（J 空间 `judgment_space_v3m_b275.json` + `g3fix` 证据，judge=`semantic_diff.py`）

```text
[coverage] J_total=1556 covered_5tuple=1151 r7_only_different=29 probe_only=0 unexecuted=0
           n/a=0 inconclusive=0 excluded=376 uncovered=405 coverage=73.97%
[coverage] semantic_failures=29 green=1151
[coverage] GATE FAIL: uncovered=405 (covered_5tuple is the only numerator; r7_only_different=29 was transferred out)
```

| 读数 | 旧 checker（2.0.0） | 新 checker（2.1.0） | 变化 |
|---|---:|---:|---:|
| J_total | 1556 | 1556 | 0 |
| **covered_5tuple** | 1180 | **1151** | **−29** |
| **r7_only_different** | （无此字段） | **29** | +29 |
| **green / EQUAL** | 1151 | **1151** | 0 |
| semantic_failures | 29 | 29 | 0 |
| excluded | 376 | 376 | 0 |
| uncovered | 376 | 405 | +29 |
| coverage_pct | 75.84% | 73.97% | −1.87pt |

产物：`D:/temp/opencode/cl_layout/gap/g3gap/coverage_g3gap.json` / `COVERAGE_G3GAP.md` /
`coverage_g3gap.log`；转出清单 `r7_transfer.json`。

### 3.4 转出条目清单（总数 29；前 20 条）

形态族：IfExp 14、Break 5、ListComp 3、GeneratorExp 3、DictComp 2、SetComp 1、While 1。
差异形状：仅嵌套 `co_consts` 值（常量拼写，如 `0` vs `False`）12 条；含嵌套 `co_code`/`co_consts.len` 17 条。
**29 条全部是 R7-only**（无任何 R1–R6 差异）。

| # | id | form | 主要差异路径（前 2 条） |
|---:|---|---|---|
| 1 | JS-IFEXP-001 | IfExp | `$.metadata.code.co_consts.v[6].co_consts.v[2].co_consts.v[0]` |
| 2 | JS-IFEXP-002 | IfExp | 同上 |
| 3 | JS-IFEXP-003 | IfExp | 同上 |
| 4 | JS-IFEXP-007 | IfExp | 同上 |
| 5 | JS-IFEXP-008 | IfExp | 同上 |
| 6 | JS-IFEXP-009 | IfExp | 同上 |
| 7 | JS-IFEXP-010 | IfExp | 同上 |
| 8 | JS-IFEXP-011 | IfExp | 同上 |
| 9 | JS-IFEXP-012 | IfExp | 同上 |
| 10 | JS-IFEXP-013 | IfExp | 同上 |
| 11 | JS-IFEXP-014 | IfExp | 同上 |
| 12 | JS-IFEXP-015 | IfExp | 同上 |
| 13 | JS-IFEXP-024 | IfExp | `…v[2].co_consts.v[1].co_code`; `….co_consts.len` |
| 14 | JS-IFEXP-025 | IfExp | `…v[2].co_consts.v[1].co_code`; `….co_consts.len` |
| 15 | JS-LISTCOMP-012 | ListComp | `…v[2].co_consts.v[1].co_code`; `….co_consts.len` |
| 16 | JS-LISTCOMP-028 | ListComp | 同上 |
| 17 | JS-LISTCOMP-029 | ListComp | 同上 |
| 18 | JS-BREAK-001 | Break | `…v[1].co_consts.v[3].co_code`; `…v[1].co_consts.v[3].co_consts.v[1].v` |
| 19 | JS-BREAK-011 | Break | 同上 |
| 20 | JS-BREAK-023 | Break | 同上 |
| … | 其余 9 条 | | `JS-BREAK-027/030`、`JS-WHILE-040`、`JS-SETCOMP-017`、`JS-DICTCOMP-019/020`、`JS-GENEXP-005/017/018` |

### 3.5 自测

- 新 `coverage_checker.py --selftest`：**13/13 通过**，含
  `r7_only_different_not_covered`、`r7_only_different_reason`、`r7_only_different_not_green`、
  `r7_plus_r1_still_covered`、`r1_only_still_covered`、`no_dimensions_keeps_old_rule`、
  `numerator_is_4`、`gate_fails_with_transfer`、`written_totals`。
  日志 `g3gap_selftest_coverage.json`。
- 既有 `coverage_checker_selftest.py`（未改）：**仍 13/13 通过**（其合成 DIFFERENT 记录没有 `diffs` 列表，
  按新规则「无可判维度 → 维持原 C1–C5 口径」，因此不受影响）。

---

## 4. 任务四：G2b / G2c 用新尺子重测

### 4.1 方法与抽样说明

- **不抽样，全量**：G2b 402/402、G2c 46/46。
- **主读数 = 冻结产品重判**：C1/C2/C3 原样取自 round9 记录，产品文本不重生成（只换尺子、产品不动），
  用当前 `semantic_diff` 重判 C4。产品哈希已逐条核验：G2c **46/46 完好**；G2b **395/402 完好，7 条漂移**。
- **第二读数 = HEAD 新反编译**（`semantic_runner` 官方链路，写入 `products_*_fresh/`，不改任何既有产品）：
  见 §4.4；说明：`semantic_runner.py` 在 `-I` 隔离模式下 `import semantic_diff` 失败（既有 CLI 缺陷，
  不在本轮可改范围），故第二读数用 `python -X utf8` 调用。
- 重判脚本 `_g3_rejudge_g2bc.py`；产物 `rejudge_g2b.json` / `rejudge_g2c.json`。

### 4.2 G2b（402 语料）

| 读数集合 | EQUAL | DIFFERENT | ERROR | 转 DIFFERENT |
|---|---:|---:|---:|---:|
| 原读数（round9，judge `dbcb1e24`） | 57 | 3 | 342 | — |
| **本轮回判（395 条哈希完好子集，judge `d31948`）** | **57** | **1** | **337** | **0** |
| 402 条全量回判（含 7 条产品漂移） | 59 | 1 | 342 | 0 |

- 唯一 DIFFERENT 仍是 `CORPUS402-0226`（`site-packages/IQEngine/interface.pyc`），差异从旧的
  `co_consts.v[10]/v[16].code_sha` 两条塌缩路径变成 **同一两个嵌套 code object 的 `co_code`**
  （R7×2），实体与旧登记一致，未新增。
- 7 条产品漂移（`c3.sha256` 与实际文件不符）：`CORPUS402-0015/0066/0324/0328/0354/0373/0377`。
  其中 round9 的两个 DIFFERENT（**0354/0373**）用现在的产品文本重判为 **EQUAL**——这是**产品文本漂移**
  （后续某轮重新反编译写进了同一产品目录），不是尺子放宽；其余 5 条仍 ERROR。
- 结论：**新尺子没有把任何 G2b 条目转成 DIFFERENT**（0 条）。G2b 仍是「57 EQUAL/1–3 DIFF/342 环境不可执行」，
  环境阻断未变，FAIL 如实。

### 4.3 G2c（46 真实 pyc）

| 读数 | 原（round9） | 新尺子（冻结产品，46/46 哈希完好） | 变化 |
|---|---:|---:|---:|
| EQUAL | 5 | **3** | −2 |
| DIFFERENT | 24 | **26** | **+2** |
| ERROR | 17 | 17 | 0 |
| 其中 DIFFERENT 仅 R7 | 19 | 21 | +2 |
| 其中 DIFFERENT 含行为差（R0–R6） | 5 | 5 | 0 |

**转 DIFFERENT 的 2 条**：

| id | 旧 | 新 | 差异 | 差异路径（前 2 条） |
|---|---|---|---|---|
| REAL46-002 | EQUAL | **DIFFERENT** | R7×24（全嵌套 `co_code`） | `$.metadata.code.co_consts.v[15].co_consts.v[2].co_code`、`…v[17].co_consts.v[3].co_code` |
| REAL46-024 | EQUAL | **DIFFERENT** | R7×7（全嵌套 `co_code`） | `$.metadata.code.co_consts.v[21].co_consts.v[5].co_code`、`…v[21].co_consts.v[6].co_code` |

两条都是**旧尺子看不见的深层嵌套函数体差异**（R1–R6 全等，仅 R7 可见），与 d22ebd6c 的「哈希塌缩」根因一致；
按新覆盖口径它们会被判为 `r7_only_different`（不计 covered，同 §3）。

### 4.4 第二读数（HEAD 新反编译产物 + 新尺子，只报读数、不修产品）

反编译到 `products_*_fresh/`（新目录，未覆盖任何既有产品），判官同一条 `semantic_diff.py`。

| 空间 | 新尺子（HEAD 产品） | 旧尺子（同一批 HEAD 产品） | 差值=纯尺子效应 |
|---|---|---|---|
| G2c（46） | EQUAL 14 / DIFF 15 / ERROR 17 | EQUAL 23 / DIFF 6 / ERROR 17 | **+9 转 DIFFERENT** |
| G2b（402） | EQUAL 59 / DIFF 1 / ERROR 342 | EQUAL 59 / DIFF 1 / ERROR 342 | **0 转 DIFFERENT** |

- G2c 的 9 条转 DIFFERENT：`REAL46-002/003/004/018/023/024/032/036/041`——旧尺子（`dbcb1e24`）对同一批产物判 EQUAL，
  新尺子（`d31948`）逐条落到嵌套 `co_code`/`co_exceptiontable` 等 R7 路径上。
- 这两个读数是**产品也变了**的口径（HEAD 反编译器比 round9 修复更多），故与 §4.2/§4.3 的「冻结产品」读数不可直接相减；
  隔离尺子效应的计算方式是「同一批产品 × 两个判官」。
- `semantic_runner` 的输出里 `covered_5tuple=0`、`module_only=29/60` 是既有设计（module-only 条目永不进覆盖分子），
  与本次口径无关。
- 原始产物：`hdr_g2c.json` / `hdr_g2b.json`、`g2c_oldjudge_freshproducts.json` / `g2b_oldjudge_freshproducts.json`。

---

## 5. 纪律与边界

- 只改两个工具；`scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/`、`core/` 零改动；
  `TOLERANCE_REGISTRY.md` 未动；`semantic_diff.py` 未动（judge sha 仍 `d31948…`）。
- **没有放宽 R7**：`_r7_only` 只用于「有 proof 时给变异分类」，`semantic_diff` 的 R7 阻断与受保护字段未变；
  覆盖口径是**收紧**（R7-only DIFFERENT 从分子转出）。
- **没有写假 proof**：4 条 proof 的依据是固定常量下的实际求值、逆汇编逐指令比对与 judge 侧 R1–R6 全等；
  `FALSE_KILL` 分支仍会拦截「proof 与行为级证据冲突」（自测方向 3 已实测）。
- 未宣称 G1/G2b/G2c/G3/G4/G6 通过；`product_complete` 仍 NOT PASS。

---

## 6. 复跑命令

```text
# 三段式自测
D:/Python/python.exe -I -X utf8 tools/completeness/mutation_test.py --selftest

# 30 案（默认：三段式 + 生成器修正）
D:/Python/python.exe -I -X utf8 .trae/.../fresh/gate_gap/_g3_run30.py --tag mut_default

# 30 案（带 4 条 proof）
D:/Python/python.exe -I -X utf8 .trae/.../fresh/gate_gap/_g3_run30.py --tag mut_proofs \
  --equivalents .trae/.../fresh/gate_gap/equivalents_g3_topcodec.json --only JS-RETURN-033,JS-RETURN-070

# 复现旧口径（保留 no-op 变异）
D:/Python/python.exe -I -X utf8 .trae/.../fresh/gate_gap/_g3_run30.py --tag mut_identity \
  --keep-identity --only JS-BREAK-001,JS-WHILE-040

# 覆盖分子重算
D:/Python/python.exe -I -X utf8 tools/completeness/coverage_checker.py \
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_b275.json \
  --evidence D:/temp/opencode/cl_layout/gap/g3fix/semantic_v3m_b275_g3fix_merged.json \
  --judge tools/completeness/semantic_diff.py \
  --out D:/temp/opencode/cl_layout/gap/g3gap/COVERAGE_G3GAP.md \
  --json D:/temp/opencode/cl_layout/gap/g3gap/coverage_g3gap.json

# G2b/G2c 冻结产品回判 / HEAD 新反编译
D:/Python/python.exe -I -X utf8 .trae/.../fresh/gate_gap/_g3_rejudge_g2bc.py both
D:/Python/python.exe -X utf8 .trae/.../fresh/gate_gap/_g3_fresh_g2bc.py both
```

## 7. 复跑记录（文件清单）

| 文件 | 内容 |
|---|---|
| `tools/completeness/mutation_test.py` | 三段式 + 生成器修正 + `--selftest` + `--keep-identity`（**唯一改动的工具之一**） |
| `tools/completeness/coverage_checker.py` | `r7_only_different` 分子修正 + `--selftest`（**唯一改动的工具之二**） |
| `fresh/gate_gap/G3_DECISIONS.md` | 本文件 |
| `fresh/gate_gap/g3_readings.json` | 全部关键读数的机器可读汇总（30 案三配置 / 覆盖 / G2b / G2c / 自测） |
| `fresh/gate_gap/COVERAGE_G3_V21.md` | 新 checker（2.1.0）对 J 空间的完整覆盖报告（含逐形态族与 405 条未覆盖明细） |
| `fresh/gate_gap/equivalents_g3_topcodec.json` | 4 条顶层 `co_code` 的 equivalence proof（含指令/偏移/常量取值） |
| `fresh/gate_gap/_g3_run30.py` | 30 案复跑驱动（默认 / `--keep-identity` / `--equivalents`） |
| `fresh/gate_gap/_g3_identity_dossier.py` | 2 条 no-op 的源码字节与 code object 对照 |
| `fresh/gate_gap/_g3_topcodec.py` | 4 条顶层 `co_code` 的逆汇编 delta |
| `fresh/gate_gap/_g3_transfer_list.py` | 29 条转出清单构建 |
| `fresh/gate_gap/_g3_rejudge_g2bc.py` / `_g3_fresh_g2bc.py` | G2b/G2c 回判与重跑 |
| `D:/temp/.../g3gap/run30_*.json` | 30 案三配置读数（`mut_default` / `mut_proofs` / `mut_identity`）；`run30_final.json` = 默认 + 4 条 proof 合并后的终态 |
| `D:/temp/.../g3gap/identity_dossier.json` / `topcodec.json` | 6 条残余的一手证据 |
| `D:/temp/.../g3gap/coverage_g3gap.json` / `r7_transfer.json` | 覆盖新读数与 29 条清单 |
| `D:/temp/.../g3gap/rejudge_g2b.json` / `rejudge_g2c.json` | G2b/G2c 冻结产品回判逐条结果 |
| `D:/temp/.../g3gap/selftest_mutation_final.json` / `g3gap_selftest_coverage.json` | 两个工具的新自测 |
| `D:/temp/.../g3gap/g3gap_legacy_mut_selftest.json` / `g3gap_legacy_cov_selftest.json` | 既有自测回归（8/9、13/13） |
