# Task 1 读数：C4 与 R7 测量口径修正（rr-v5r01）

日期：2026-10-24 · 基线 commit `e755d773` · 工作目录 `.trae/specs/achieve-any-syntax-completeness/rounds/round11/task1/`

## 1. 口径变化（1.1–1.3）

| 项 | 旧行为 | 新行为 |
|---|---|---|
| 1.1 calls | `semantic_runner` 忽略 `input_model.calls`，全部按 module-only 判 | 读取 `input_model.calls`（表达式字符串），经 case `call_exprs` 传入 `semantic_diff`，在模块命名空间逐条求值，R1–R6 观测真实调用 |
| 1.1 module-only | 无 calls 的 EQUAL 记 `covered_5tuple`（假绿） | 无 calls 条目记 `status=probe_only`、`reason=module_only`，C4 verdict 保留作缺陷证据，**永不**进覆盖分子；summary 增加 `module_only`、`covered_5tuple` 计数 |
| 1.2 R7 | `tolerance.ignore_metadata_fields` 可静默忽略任意 metadata 路径（含 co_code/co_consts/co_exceptiontable） | 三字段 + 子路径 + 祖先路径受硬保护；试图忽略直接判 `ERROR`（`unregistered R7 tolerance`）；自定义忽略路径完整写入结果 `tolerances` 供审计；书面台账见 `TOLERANCE_REGISTRY.md` |
| 1.3 超时 | 原侧超时 → `ERROR`；产物侧超时 → `TERMINATION` diff → `DIFFERENT` | 任一侧超时 → `INCONCLUSIVE`（`original/product execution timed out`），不记 EQUAL/DIFFERENT、不覆盖 |

`co_code` / `co_consts` / `co_exceptiontable` 差异默认判 `DIFFERENT`（原行为保留，现不可被 tolerance 关闭）。

## 2. 自测（1.5，四类口径）

| 自测 | 结果 | 覆盖 |
|---|---|---|
| `semantic_diff_selftest.py` | **26/26 PASS**（原 17 + 新 9） | module-only（`module-only-equal`）、calls（`call-exprs-equal/r1/missing-function`）、R7（`r7-plus-r1`=R1+R7 同现、`r7-protected-tolerance`/`r7-ancestor-tolerance`=未登记 tolerance 拒绝）、timeout（`timeout-product`/`timeout-original`→INCONCLUSIVE+timed out） |
| `semantic_runner_selftest.py`（新增） | **11/11 PASS** | runner 路径：无 calls → `probe_only+module_only`、不覆盖；有 calls → 传递、执行、`covered_5tuple`；summary 计数 |

回归：`mutation_test_selftest`、`fuzz_selftest`、`coverage_checker_selftest`、`gate_report_selftest`、`rule_manifest_selftest` 全部 exit 0；`freeze_check.py` 5/5 PASS（比较器 SHA 未变）。

## 3. J 样本重跑（1.4）

### 3.1 as-is（round9 原空间，无 calls）

```
python -X utf8 tools/completeness/semantic_runner.py --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --out j_sample_asis/semantic_j_sample_asis.json --report j_sample_asis/summary.json --product-dir j_sample_asis/semantic_products --limit 100 --timeout 15 --seconds 240
```

读数：`records=51 verdicts={EQUAL:45, DIFFERENT:6} skipped={c1_source_missing:49} stopped=skipped module_only=51 covered_5tuple=0`

- verdicts 与基线（round11/baseline_before/j_sample）**逐项一致**：45 EQUAL / 6 DIFFERENT（JS-IF-017/021/076/088/090/097）——判据修改零回归。
- 51 条全部 `probe_only + module_only`，`covered_5tuple=0`：module-only 假绿消除（旧口径下 45 条 EQUAL 曾计为覆盖）。

### 3.2 calls 填充（`j_sample_calls_input.json`，6 条 DIFFERENT 补 calls）

```
python -X utf8 tools/completeness/semantic_runner.py --space j_sample_calls_input.json --out j_sample_calls/semantic_j_sample_task1.json --report j_sample_calls/summary.json --product-dir j_sample_calls/semantic_products --limit 100 --timeout 15 --seconds 240
```

读数：`records=51 verdicts={EQUAL:45, DIFFERENT:6} skipped={c1_source_missing:49} stopped=skipped module_only=45 covered_5tuple=6`

| 条目 | calls | verdict | dims | 结论 |
|---|---|---|---|---|
| JS-IF-017/021/088/090/097 | `v_nest_fin_continue([[0, 1]])`; `v_nest_fin_continue([0])` | DIFFERENT | **R7+R1×6** | **R1（B142）出现，不再仅 R7** ✓ |
| JS-IF-076 | `if_in_for(); if_in_try(); if_shallow(); if_in_match()` | DIFFERENT | R7×5（函数体 code_sha/consts_len 差） | 带调用证据的函数体差异，不再被 module-only 掩盖 ✓ |

详细路径证据（`detail/result_js_if_017.json`、`detail/result_js_if_076.json`）：

- 017：`R1 $.call[0].return.len orig=3 prod=2`（原件 `[1,2,[0,1]]` vs 产物 `[1,[0,1]]`）；`R1 $.call[1].return.len orig=2 prod=5`（原件 `[1,2]` vs 产物 `[1,1,2,1,0]`，continue 路径）；`R7 $.metadata.code.co_consts.v[2].code_sha`（嵌套函数字节码差）。R7 与 R1 同现，按 DIFFERENT 计失败（spec「R7 与 R1 同时出现」场景）。
- 076：`R7 $.metadata.code.co_consts.v[2]/v[3]/v[6]` 的 `code_sha`/`consts_len`（`if_in_while` break 丢失、`if_in_try`/`if_shallow`/`if_in_match` 结构差）；四个调用 R1 全等（返回 1/3/0/5）——调用未掩盖 R7，R7 保留函数体差异信号。

### 3.3 `if_in_while()` 排除决定

076 的 calls 故意不含 `if_in_while()`：当前产物丢失 `break` 后 `while True: R = 1` 不终止，调用会把 5 条 R7 函数体证据变成超时 INCONCLUSIVE（口径 1.3），反而掩盖缺陷。`if_in_while()` 的终止性与返回值（原件 `return 2`）证据归 Task 3 修复后验证。

## 4. 输入与产物清单

| 文件 | 说明 |
|---|---|
| `build_calls_input.py` | 生成 calls 填充样本（round9 原空间不动） |
| `j_sample_calls_input.json` | 100 条工作副本，6 条带 calls |
| `j_sample_asis/` | as-is 重跑（51 记录 + summary + products） |
| `j_sample_calls/` | calls 重跑（51 记录 + summary + products） |
| `detail/` | 017/076 单案详细差分（case + result） |

## 5. 结论

- 1.1 ✓ calls 传递 + module_only 分类（covered_5tuple=0 → 假绿消除）
- 1.2 ✓ R7 三字段默认 DIFFERENT + 未登记 tolerance 拒绝 + 书面台账
- 1.3 ✓ 超时双侧 INCONCLUSIVE
- 1.4 ✓ 五条 B142 出现 R1；076 函数体差异带调用证据
- 1.5 ✓ 四类口径自测全绿 + 7 项工具自测回归全绿
- 1.6 提交 `rr-v5r01:`（见 git log）
