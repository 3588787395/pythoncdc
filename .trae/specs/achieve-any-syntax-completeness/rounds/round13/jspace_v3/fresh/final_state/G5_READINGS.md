# G5 回归读数（fresh 复跑，2026-11-16）

> 目标：按 `spec.md` 第 124 行「命令面」把 G5 五项补齐为完整读数（此前只跑过 pytest）。
> **只读承诺**：未修改 `core/`、`scripts/`、`tests/` 与任何已提交证据；全部产物写在
> `D:\temp\opencode\cl_layout\g5\` 与本 `final_state/` 目录。
> 判据唯一入口仍是冻结的 `scripts/pyc_verify.py`（SHA256 与 spec.md:136 期望值逐字符一致）。

- 仓库：`F:\Downloads\pythoncdc-main`，HEAD `f59fc775`（rr-v5r185），`git status -- core/cfg` 为空
- 解释器：`D:/Python/python.exe` → CPython **3.11.7** (MSC v.1937 64-bit)
- 比较器：`scripts/pyc_verify.py` = `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4`（== spec 期望）
- 外部 `compare_pyc`：`D:/Desktop/ptrade相关/pylingual/pylingual/equivalence_check.py`，sha256 前缀 `9c7567bd6776b36b`（与 `g5_rerun/G5_RERUN.md` 记录一致）
- 环境变量：`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1`；**未用 `-I`**（`-I` 会把 cwd 移出 `sys.path`，`core` 不可导入；故沿用历史做法：`cwd=仓库根` + `python -m pytest`，无需包装器）

---

## 一、输入存在性核对（Test-Path，逐条）

| 输入 | 结果 | 大小 |
|---|---|---|
| `baseline/shards/shard0.json` | EXISTS | 10,191 B |
| `baseline/shards/shard1.json` | EXISTS | 10,246 B |
| `baseline/shards/shard2.json` | EXISTS | 12,664 B |
| `baseline/shards/shard3.json` | EXISTS | 10,551 B |
| `baseline/shards/shard4.json` | EXISTS | 11,890 B |
| `baseline/shards/shard5.json` | EXISTS | 13,678 B |
| `baseline/shards/shard6.json` | EXISTS | 11,300 B |
| `baseline/shards/shard7.json` | EXISTS | 8,952 B |
| `baseline/small34_index.json` | EXISTS | 6,105 B |
| `site-packages/fly/data/quotation.pyc` | EXISTS | 209,494 B |
| `scripts/pyc_verify.py` | EXISTS | 18,122 B |
| `tests/test_algorithm_correctness.py` | EXISTS | 44,621 B |
| `tests/test_deep_nesting_pressure.py` | EXISTS | 14,088 B |
| `tests/test_control_flow_completeness_matrix.py` | EXISTS | 31,175 B |
| `tests/test_complete_syntax_coverage.py` | EXISTS | 41,244 B |
| `tests/test_boundary_cases.py` | EXISTS | 22,010 B |
| `tests/test_core_functional.py` | EXISTS | 13,167 B |
| `rounds/round9/VERIFICATION.md`（IV.2 §三） | EXISTS | 6,551 B |

**MISSING = 0**。索引/文件/套件/IV.2 文档全部在位。

### 但索引**内部**的 `path` 字段是陈旧绝对路径（这一条必须先说清）

`shard*.json` 每条 entry 形如：

```json
{"path": "D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQCommon/__init__.pyc",
 "rel": "IQCommon/__init__.pyc", "function_count": 2, "size": 1630}
```

`pyc_verify.py:143` 只读 `path`，因此**按 spec 字面直接跑会在第一条就 fatal**（见 §2.1 实测 rc=1）。
处理方式与 `fresh/g5_rerun/` 完全一致、并且只改 `path` 一个字段（`rel`/`size`/`function_count` 全部冻结）：

- 脚本：`D:\temp\opencode\cl_layout\g5\remap_indexes.py`（把 `path` 重映射到本检出 `site-packages/<rel>`）
- 输出：`D:\temp\opencode\cl_layout\g5\remapped\{shard0..7}.json`、`small34.json`、`remap_report.json`
- 校验结果：**436/436 entry 存在，`missing_total=0`、`size_mismatch_total=0`**（402 + 34）
- `remap_report.json` SHA256 = `48C79CDF04E3132F8EE1DD8CE82F044873AEDF6AF7D5ECB362168F96ED404F4B`

即：**语料本体完好、字节长度与冻结值全等**，缺失的只是路径前缀，不是语料缺失。这不是"环境问题"的辩解，而是索引字段 machine-bound 的事实（`g5_rerun/G5_RERUN.md` §Why 已记录过同一现象）。

---

## 二、五项逐条读数

### 2.1 项①：402 八分片 batch

**A. spec 字面命令（原样，未 remap）**

```text
python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/shards/shard0.json
```
- exit code：**1**
- 输出：`[fatal] pyc 不存在：D:\admin\.qoder\worktrees\app\f557fd\pythoncdc-main\site-packages\IQCommon\__init__.pyc`
- 判定：**命令面按字面不可执行**（索引陈旧路径），非产品读数；分片 1–7 同因同果，未逐片重复消费时间
- 日志：`out\probe_shard0_literal.log`

**B. remap 后（历史既定方法，与 `g5_rerun` 同）**

```text
python -X utf8 scripts/pyc_verify.py batch --index D:\temp\opencode\cl_layout\g5\remapped\shardN.json --json out\shardN_report.json   (N=0..7)
```

| 分片 | exit | 文件 | 单元 | 状态桶 | 耗时 |
|---|---|---|---|---|---|
| shard0 | 0 | 51 | **786/786** | success 51 / failure 0 / compile_error 0 / error 0 | 45.5 s |
| shard1 | 0 | 51 | **469/469** | success 51 / 0 / 0 / 0 | 28.5 s |
| shard2 | 0 | 51 | **538/538** | success 51 / 0 / 0 / 0 | 24.5 s |
| shard3 | 0 | 51 | **887/887** | success 51 / 0 / 0 / 0 | 32.5 s |
| shard4 | 0 | 51 | **855/855** | success 51 / 0 / 0 / 0 | 31.8 s |
| shard5 | 0 | 51 | **999/999** | success 51 / 0 / 0 / 0 | 29.8 s |
| shard6 | 0 | 51 | **801/801** | success 51 / 0 / 0 / 0 | 40.4 s |
| shard7 | 0 | 45 | **1282/1282** | success 45 / 0 / 0 / 0 | 102.5 s |
| **合计** | — | **402** | **6617/6617（100.0000%）** | **success 402 / failure 0 / compile_error 0 / error 0** | **335.5 s** |

- 逐片单元数 786/469/538/887/855/999/801/1282 与 `g5_rerun` 记录**逐一相同**（和 = 6617）
- 文件数 51×7 + 45 = **402**，与历史口径一致
- **失败样本清单：0 条**（0 个文件 status≠success，0 个失败单元）
- 与历史基线 **6617/6617 对比：±0**
- 日志：`out\shard0..7.log`、报告 `out\shard0..7_report.json`

### 2.2 项②：small34 batch

```text
python -X utf8 scripts/pyc_verify.py batch --index D:\temp\opencode\cl_layout\g5\remapped\small34.json --json out\small34_report.json
```
- exit code：**0**
- 读数：**34/34 文件 success，1568/1568 单元（100%）**，failure/compile_error/error = 0
- 耗时：**309.0 s**（报告内 `elapsed_sec` 306.1）
- 失败样本：**0 条**
- 与历史基线 **1568/1568 对比：±0**
- 日志：`out\small34.log`，报告 `out\small34_report.json`

### 2.3 项③：quotation 单验

```text
python -X utf8 scripts/pyc_verify.py single site-packages/fly/data/quotation.pyc
```
- exit code：**0**
- 读数：`status=success units=153/153 success_rate=100.00%`
- 耗时：**50.2 s**
- 产物侧提示：未加 `--source`，比较的是就地 `quotationOK.py`（脚本自身打印 NOTE；与历史 G5 口径相同，不重生成）
- 与历史基线 **153/153 对比：±0**
- 日志：`out\quotation.log`

### 2.4 项④：pytest

**(a) spec.md:124 字面命令 → 不可执行（命令面笔误）**

```text
python -X utf8 -m pytest -q tests/test_algorithm_correctness.py test_deep_nesting_pressure.py \
  tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py \
  tests/test_boundary_cases.py tests/test_core_functional.py
```
- exit code：**4**
- 输出：`ERROR: file or directory not found: test_deep_nesting_pressure.py` / `no tests ran in 0.33s`
- 原因：spec 原文第二个套件**漏了 `tests/` 前缀**（其余五个都有）。这是 spec 文本缺陷，不是环境或产品问题；按字面复制粘贴的读者会得到 rc=4。**如实标红**
- 日志：`out\pytest_spec_literal.log`

**(b) 修正路径后：六套件（spec 意图的六个文件）**

```text
python -X utf8 -m pytest -q tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py \
  tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py \
  tests/test_boundary_cases.py tests/test_core_functional.py
```
- exit code：**1**
- 读数：**2 failed, 277 passed, 2 xpassed**（pytest 自报 `in 41.61s`，墙钟 50.3 s）
- 失败恰为冻结对（共 **2 条**，全列）：
  1. `tests/test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`
  2. `tests/test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function`（`AssertionError: ... 原始源码语法无效`）
- 与 round9 §一.4 **六套件 277 passed 对比：±0**

**(c) 七套件（gate 期望 282 的口径，含 `tests/test_repo_tool_hygiene.py`）**

```text
python -X utf8 -m pytest -q <六个 tests/ 文件> tests/test_repo_tool_hygiene.py -p no:cacheprovider --tb=no
```
- exit code：**1**
- 读数：**2 failed, 282 passed, 2 xpassed**（`in 60.23s`，墙钟 69.0 s）
- 失败为**同一冻结对**（2 条，同上）
- 与任务给定基线 **2F/282P/2XP 对比：±0，失败名逐条一致**

> 口径说明（有证据，不是辩解）：277 与 282 的差**恰是卫生套件 5 个用例**（286 收集 = 2+282+2；281 收集 = 2+277+2）。
> 六套件 277 与 round9 存档读数一致；282 是七套件读数。两个数都是实测，谁也没被凑。
> 结论：**pytest 项相对历史 277（六套件）与 282（七套件）均无回退**。

### 2.5 项⑤：IV.2 自检（round9 VERIFICATION.md §三）

| §三 项 | 期望 | 本次读数 | 判定 |
|---|---|---|---|
| IMPORT_OK | true | **true**（导入 `core.pyc_loader_v2, core.control_flow, core.cfg, core.cfg.region_analyzer, core.cfg.region_ast_generator, core.astree, core.ast_nodes, core.pyc_objects, core.fast_stack, core.bytecode_matcher`） | ✓ |
| COMPILE_OK | true | **true**（两文件 `py_compile` 通过 + `ast.parse(encoding='utf-8-sig')` 通过） | ✓ |
| BOM 单头（`region_ast_generator.py` / `region_analyzer.py`） | `one` / `one` | **`none` / `none`**（`efbbbf` 计数 0；文件首字节 `"""` + CRLF） | ✗ **红** |
| CRLF 原样 | 保持 CRLF | 78,471/78,471 与 39,463/39,463 行全 CRLF，**孤立 LF = 0** | ✓ |
| 无遗留插桩 `print(` | 0 | 全文件 19 处（17 + 2，均为既有常规输出，非调试插桩；未新增行可归因——`core/cfg` 与 HEAD clean） | ✓* |
| `TODO/FIXME/XXX_DEBUG` | 0 | **0** | ✓ |
| G3 前缀（gate 定义：`git diff HEAD` 的**新增行**） | 0 | **0**（`core/cfg` 无未提交改动，新增行集为空） | ✓ |
| G3 前缀（整文件粗扫，更严口径） | 0 | **2**，均为 HEAD 既有方法：`_merge_block_is_then_exclusive`（L28396）、`_merge_block_is_loop_back_edge`（L56858）——**非本轮新增** | ✓*（口径差已在案） |
| G4 特判（按文件名/函数名、绝对偏移、长度计数门控） | 0 | 文件名门控 0、绝对偏移门控 0、长度计数门控 0；`co_name/name == ...` 命中 21，抽样全是**字节码语义比较**（如 `co_name == '<module>'`、`name == 'JUMP_FORWARD'`），非"按测试名/文件名开后门" | ✓ |
| 尺子自检（`selfcheck quotation.pyc`） | 自证全等 ∧ 两变异各抓到 | `自证：153/153 单元 Equal`、`常量 抓到 1/153`、`极性 抓到 1/153`、`OK —— 判据可用` | ✓ |
| `core/cfg` clean | 空 | 空 | ✓ |

**BOM 项是真红，且不是本次运行造成的**（实证）：

- 工作区两文件 `raw.startswith(b'\xef\xbb\xbf') == False`，`bom_count == 0`；`raw/sources/` 副本同样无 BOM
- `git show HEAD~50:core/cfg/region_ast_generator.py` → **BOM=True**；`git show HEAD:` → **BOM=False**
- 逐个提交探针定位：`37cb12e7`（rr-v5r164）BOM=True → `a1de8c5f`（rr-v5r165，全 sha `a1de8c5f136f0cc8032b4c13fae7261c0288c049`）起两文件 BOM 均为 False，并一直保持到 HEAD
- 因此：这是 **rr-v5r165 起就存在的已提交状态漂移**，与本次 G5 复跑无关；但它确实使 §三「BOM 单头」判据自那时起不再满足

**项目自带判据的裁决（证据）**：用本次真实读数拼出 gate 载荷并调用 `tools/completeness/gate_report.py::gate_g5`：

```text
gate_g5 实读数      -> status = FAIL   (units 6617/6617、small34 1568/1568、quotation 0、
                                        tests "2 failed, 282 passed, 2 xpassed in 60.23s" 均绿；
                                        仅 BOM=none/none 一项不满足)
gate_g5 BOM 反事实  -> status = PASS   (其余字段完全相同，只把 BOM 置回 "one")
```

即 **BOM 是当前唯一阻断项**，其余字段与 rr-v5r77 基线逐项相同。载荷与裁决：
`out\g5_gate_payload.json`（SHA256 `147DE6B8E69511895B6DD455B3ADAC39187F8ABFE54A5050BEE9D1563DE428A7`）、
`out\g5_gate_payload_bom_counterfactual.json`、`out\gate_verdict.log`。

> 处置建议（本次**未执行**，因 `core/cfg` 与判据均属禁改范围）：二选一并留痕——(i) 在 `core/cfg` 两文件恢复单个文件首 BOM 并单独提交；
> (ii) 修订 `gate_g5` 的 IV.2 判据（`== "one"` 改为"至多一个且仅在首"），并同步 `round9/VERIFICATION.md` §三 的期望描述。
> 在二者落地前，任何"G5 = PASS"的声明都与项目自带 gate 的返回值矛盾。

---

## 三、与规范期望阈值总对照

| 项 | 规范/历史期望 | 本次实测 | 差值 | 判定 |
|---|---|---|---|---|
| 402 八分片 | 6617/6617（402/402 success） | **6617/6617**（402/402，0 failure） | **±0** | 🟢 |
| small34 | 1568/1568（34/34） | **1568/1568**（34/34） | **±0** | 🟢 |
| quotation | 153/153 | **153/153** | **±0** | 🟢 |
| pytest（七套件，gate 口径） | 2F/282P/2XP | **2F/282P/2XP**，失败为同一冻结对 | **±0** | 🟢 |
| pytest（六套件，spec 文件面） | round9：2F/277P/2XP | **2F/277P/2XP** | **±0** | 🟢 |
| pytest（spec 字面命令） | 应可执行 | **rc=4，未收集到用例**（`test_deep_nesting_pressure.py` 缺 `tests/`） | 命令不可执行 | 🔴 |
| 402 命令面 | 应可直接执行 | 字面 **rc=1 `[fatal] pyc 不存在`**（索引含陈旧绝对路径） | 需 remap 才能测 | 🔴（命令面，非产品读数） |
| IV.2 IMPORT/COMPILE/CRLF/G3/G4/尺子/clean | 全绿 | 全绿（口径差异已标注） | ±0 | 🟢 |
| IV.2 BOM 单头 | `one`/`one` | **`none`/`none`** | **−1（自 rr-v5r165）** | 🔴 |

**没有任何一项产品读数低于历史**（402 / small34 / quotation / pytest 四项全等）。两处红是
**命令面缺陷**（spec 笔误、索引陈旧路径）与 **IV.2 BOM 判据自 rr-v5r165 起的已提交漂移**，
均附实证，未以"环境问题"搪塞。

---

## 四、失败样本清单（规模 + 明细）

| 来源 | 总数 | 明细 |
|---|---|---|
| 402 八分片 batch | **0** | 无 |
| small34 batch | **0** | 无 |
| quotation single | **0** | 无 |
| pytest（六/七套件） | **2** | 全列于 §2.4(b)，冻结对 `B01_simple_if_then_else_merge`、`BOUNDARY_02_large_function` |
| pytest（spec 字面） | **N/A** | 收集阶段失败，无用例执行 |

未出现"多到需截前 30 条"的失败集，故未截断。

---

## 五、耗时汇总（墙钟）

| 步骤 | 耗时 |
|---|---|
| 402 八分片 ×8 | 45.5 + 28.5 + 24.5 + 32.5 + 31.8 + 29.8 + 40.4 + 102.5 = **335.5 s** |
| small34 | **309.0 s** |
| quotation single | **50.2 s** |
| pytest 六套件 | **50.3 s**（自报 41.61 s） |
| pytest 七套件 | **69.0 s**（自报 60.23 s） |
| pytest spec 字面 | **10.6 s** |
| IV.2 静态自检 | **30.0 s** |
| 尺子 selfcheck | **≥120 s**（转后台跑完，未单独计秒） |
| remap 索引 | ~2 s |
| **主链合计（不含 selfcheck）** | **≈ 854 s ≈ 14.2 min** |

---

## 六、边界与未掩盖项

1. **batch 的 rc 语义**：`cmd_batch` 仅在 `error`/`compile_error` 桶非空时返回 1；`failure` 文件**不会**让 rc≠0。故本报告一律以 `units_success/units_total` 与 `files_by_status` 为读数，不以 rc 代替绿。
2. **未重生成产物**：项①–③ 比较的是就地 `*OK.py`，与 rr-v5r06 以来既定 G5 口径一致（脚本自己打印 NOTE）。这是既定方法，不是新鲜反编译证明。
3. **stderr 噪声**：`shard7`/`small34` 日志尾部有大量 `SyntaxWarning: "is" with a literal`，来自 `load_dailyOK.py:385`、`hsidOK.py:19` 等**产物文本**的编译告警，不影响单元判定（这些文件所在分片仍 100% success）。shard7 耗时偏高（102.5 s）与告警/大文件规模相关，未进一步归因。
4. **G3/G4 口径**：gate 用 `git diff HEAD` 新增行做 G3；我用整文件粗扫做交叉核验（G3=2 个既有 def、G4 文件名/偏移/长度门控=0）。两个口径都记录，避免"读数好看是因为口径松"。
5. **`-I` 问题**：按任务提示未使用 `-I`。若必须 `-I`，需显式 `PYTHONPATH=<repo>` 或用包装器把 cwd 注入 `sys.path`——本次路径下 `python -m pytest` 已足够。

---

## 七、证据文件清单（`D:\temp\opencode\cl_layout\g5\`）

| 文件 | 说明 |
|---|---|
| `out\g5_summary.json` | 全部条目机读汇总（SHA256 `70A914B22C8237D6D9545FCAC2000E6760836187C307019C5EBFF7A396F2BB04`） |
| `out\shard0..7_report.json`、`out\small34_report.json` | `pyc_verify.py batch` 原始报告（含 rows 逐文件/逐单元） |
| `out\shard0..7.log`、`out\small34.log`、`out\quotation.log` | 各命令 stdout/stderr + rc + 耗时 |
| `out\pytest_spec_literal.log` | spec 字面 pytest（rc=4） |
| `out\pytest_six_files.log` | 六套件（2F/277P/2XP） |
| `out\pytest_seven_files.log` | 七套件（2F/282P/2XP） |
| `out\iv2_check.json`、`out\iv2_check.log` | IV.2 全部机读项（SHA256 `AE685A106E8914A55E873896A9457989809F856292488EA32EF21120BEBB2D65`） |
| `out\ruler_selfcheck.log` | 尺子自证 153/153 + 双变异（SHA256 `6A9889C9D81258BA148AD40C90C285779B9D682C1C52AE6E53D6EB565192FB7F`） |
| `out\g5_gate_payload.json`、`out\g5_gate_payload_bom_counterfactual.json`、`out\gate_verdict.log` | gate_g5 裁决与反事实 |
| `remapped\shard0..7.json`、`remapped\small34.json`、`remapped\remap_report.json` | 仅 `path` 重映射后的索引与校验报告 |
| `remap_indexes.py`、`run_g5.py`、`iv2_check.py`、`run_gate.py` | 本次用到的只读脚本 |

---

## 八、一句话结论

**G5 的四项功能读数全部与历史持平（402 6617/6617、small34 1568/1568、quotation 153/153、
pytest 2F/282P/2XP），零回退；但 G5 整体按项目自带 `gate_g5` 判定为 FAIL，唯一阻断项是
IV.2 的 BOM 判据（`none/none` vs 期望 `one/one`，源头为已提交提交 `a1de8c5f` / rr-v5r165），
另有两条命令面缺陷（spec 第 124 行 pytest 路径漏 `tests/`、402 索引内 `path` 为陈旧绝对路径需 remap）。**
