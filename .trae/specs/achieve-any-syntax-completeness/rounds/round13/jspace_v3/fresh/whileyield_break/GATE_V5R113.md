# GATE_V5R113 — rr-v5r113 全量回归闸门读数、逐案对比与抖动归因

## 0. 元信息与复现命令

- 修复前 HEAD：`d742d4d0`（rr-v5r112）。待验证改动：`core/cfg/region_ast_generator.py`
  `+7 / -0`，标记 `[v113-WYBREAK]`（6 行注释 + 1 行 `_ii = _instr_idx`）。
- Python：`D:/Python/python.exe`（3.11.7）；runner：`tools/completeness/semantic_runner.py`。
- 判官：`tools/completeness/semantic_diff.py` SHA256 =
  `DBCB1E246DD549F2C66A1D779F31EBA0506F9C99364DB02A679523DDE84D8174`，
  与 v5r112 三分片/46 sweep payload 的 `judge_sha256` 逐字一致（可比性成立）。
- 输入 space：`fresh/judgment_space_v3m_applied.json`（1556 entries，seed=0）；
  分片边界与 v5r112 首条记录 id 逐一对齐（idx0 `JS-IF-001`、idx519
  `JS-NONLOCAL-030`、idx1038 `JS-RETURN-028`）。
- 三个分片**串行**执行（避免 2 核并发抖动），cwd = repo 根 `F:/Downloads/pythoncdc-main`：

```
D:/Python/python.exe tools/completeness/semantic_runner.py \
  --space  .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_applied.json \
  --out    .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_shard{i}_v5r113.json \
  --report .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/semantic_shard{i}_v5r113_report.json \
  --product-dir D:/temp/opencode/cl_layout/r113gate/v113_shard{i} \
  --offset <0|519|1038> --limit <519|519|518> --timeout 20
```

46 sweep（全量，无 offset/limit）：

```
D:/Python/python.exe tools/completeness/semantic_runner.py \
  --space  .trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json \
  --out    .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/whileyield_break/semantic_46_v5r113.json \
  --report .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/whileyield_break/semantic_46_v5r113_report.json \
  --product-dir D:/temp/opencode/cl_layout/r113gate/v113_46 --timeout 20
```

- 所有中间产物（反编译产品 `.py`、逐案对比脚本与结果、单案复跑 json、runner
  日志）一律写 `D:/temp/opencode/cl_layout/r113gate/`，**不落证据目录、不入库**。
  入库的仅为 6 个闸门 json/report、本证据目录内的 46 sweep json/report 与本文档。
- runner 的 `rc=3` 是「存在 ERROR verdict」的正常返回码，非失败（基线本身含 ERROR）。

## 1. 冻结不变式（闸门前置核验，全部通过）

| 项 | 实测 | 结论 |
|---|---|---|
| `scripts/pyc_verify.py` SHA256 | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` | 与冻结值逐字一致 |
| `tools/completeness/semantic_diff.py` SHA256 | `DBCB1E24…D8174` | 与 v5r112 `judge_sha256` 一致 |
| `git diff -- tests/ scripts/pyc_verify.py tools/completeness/semantic_diff.py` | 空 | 零改动 |
| `git status --short -- core parsers bytecode` | 仅 `M core/cfg/region_ast_generator.py` | 唯一已跟踪改动 |
| `git diff -- core/cfg/region_ast_generator.py` | `+7 / -0`，`:16113` YIELD_VALUE 分支新增 `_ii = _instr_idx` | 与 `[v113-WYBREAK]` 声明一致；既有 `_yv_nx/_yv_nn/_yv_bind` 扫描逻辑逐字不改 |

## 2. 1556 J 空间三分片全量语义闸门

### 2.1 分片读数（v5r113 实测 vs v5r112 基线）

| 分片 | offset/limit | v5r112 基线 | v5r113 实测 | 校正基线 |
|---|---|---|---|---|
| shard0 | 0 / 519 | EQUAL 367 / ERROR 151 + NO_C4 1 | **EQUAL 367 / ERROR 152** | 367 / 152 |
| shard1 | 519 / 519 | EQUAL 405 / INCONCLUSIVE 1 / ERROR 110 + NO_C4 3 | **EQUAL 406 / ERROR 113** | 406 / 113 |
| shard2 | 1038 / 518 | EQUAL 407 / ERROR 111 | **EQUAL 407 / ERROR 111** | 407 / 111 |
| 合计 | 1556 | EQUAL 1179 / ERROR 372 / INCONCLUSIVE 1 / NO_C4 4 | **EQUAL 1180 / ERROR 376** | EQUAL 1180 / ERROR 376 |

v5r113 三分片读数与「抖动校正后」的 v5r112 / v5r111 / v5r110 / v5r89 基线
逐分片、逐案一致（`EQUAL 1180 / ERROR 376`）。

### 2.2 逐案 c4 verdict 对比（compare_v5r113.py，1556 案全覆盖）

- 案数：v5r112 1556 / v5r113 1556；`只在 old = []`、`只在 new = []`。
- **逐案变化 = 5**，按等级粗分 **变差 0 / 变好 5 / 同级 0**：

| case | v5r112 | v5r113 | 归因 |
|---|---|---|---|
| `JS-AWAIT-008` | INCONCLUSIVE | EQUAL | 一次性执行超时抖动恢复 |
| `JS-BOOLOP-011` | NO_C4 | ERROR | `decompile_failed`（反编译 20s 超时） |
| `JS-WHILE-023` | NO_C4 | ERROR | `decompile_failed`（历史需 `--timeout 120` 的同族抖动案） |
| `JS-WITH-016` | NO_C4 | ERROR | `decompile_failed` |
| `JS-WITH-083` | NO_C4 | ERROR | `decompile_failed` |

- **总变化 5 / 回归 0 / 改善 5、0 真实回归**。
- 5 个案的 v5r112 记录 `note` 均为 `TimeoutExpired … timed out after 20.0
  seconds`（反编译）或 `original execution timed out`（判官），与 rr-v5r112
  已登记的 10 个并发抖动案同族；与 `[v113-WYBREAK]` 的 YIELD_VALUE 循环
  header 路径无关（均为 site-packages 大 pyc / real-package module 与
  Linux `.so` 阻断案）。

### 2.3 抖动案单案无并发复跑（历史纪律）

对 5 个变化案各以 `--offset <global_idx> --limit 1 --timeout 20` 单案复跑
（idx：JS-AWAIT-008=537、JS-BOOLOP-011=128、JS-WHILE-023=901、
JS-WITH-016=684、JS-WITH-083=751），结果 `recheck_v5r113_result.json`：

| case | 基线 | 全量 | 单案 t20 |
|---|---|---|---|
| JS-AWAIT-008 | INCONCLUSIVE | EQUAL | **EQUAL** |
| JS-BOOLOP-011 | NO_C4 | ERROR | **ERROR** |
| JS-WHILE-023 | NO_C4 | ERROR | **ERROR** |
| JS-WITH-016 | NO_C4 | ERROR | **ERROR** |
| JS-WITH-083 | NO_C4 | ERROR | **ERROR** |

**5/5** 单案复跑结果与全量读数一致，且与抖动校正基线（EQUAL 1180 /
ERROR 376）逐案逐字一致；无案需要 `--timeout 120` 升级（本轮串行执行，
反编译全部在 20s 内完成）。据此判定 5 个变化全为已登记并发/超时抖动，
非修复引起的真实回归。

### 2.4 重点关切：循环 header 含 YIELD_VALUE 的生成路径

修复只改 `_loop_process_header_instructions` 的 YIELD_VALUE 分支索引锚点，
需确认「没有把原本能生成的循环改成别的产品文本」。逐案比对了全部 1556
案的 `c3.sha256`（产品文本哈希）：

- 产品 sha 变化 = **4**，且这 4 个案全部是「v5r112 NO_C4（无产品）→
  v5r113 生成产品」的抖动案（同上表 4 个 NO_C4 案）。
- **不存在「c4 verdict 不变但产品文本变化」的案**：所有原本 EQUAL /
  ERROR / DIFFERENT 且有产品的 1552 案，产品文本逐字节不变。
- 结论：修复未触碰任何原本能正常生成的产品文本；零产品漂移。

## 3. 46 真实 pyc sweep

- 输入 `.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json`
  （46 entries），`skip1 = REAL46-045 c2_pyc_missing` 成立
  （`scripts/__pycache__/pyc_verify.cpython-311.pyc` 缺失），得 45 records。
- 读数：

| | DIFFERENT | EQUAL | ERROR | skip |
|---|---|---|---|---|
| v5r112 基线 | 11 | 17 | 17 | 1 |
| **v5r113 实测** | **10** | **18** | **17** | **1** |

  与预期 `10 DIFFERENT / 18 EQUAL / 17 ERROR + skip1` 完全一致。
- **逐案 c4 verdict 变化 = 1，唯一变化 `REAL46-019 DIFFERENT → EQUAL`**：
  - v5r112 `c4 = {"verdict":"DIFFERENT","diffs":["R7"],…}`（唯一 R7
    `$.metadata.code.co_consts.v[19].code_sha`）；
  - v5r113 `c4 = {"verdict":"EQUAL","diffs":[],…}`（`diffs=[]`）。
  - 其余 44 案逐案零变化；`只在 old = []`、`只在 new = []`；0 NO_C4。
- 产品文本 `c3.sha256` 变化同样 **仅 REAL46-019 一案**
  （`6f7468d5…` → `38b8e1f0…`），其余 44 案产品逐字节不变。
- REAL46-001 / 004 / 036 维持 EQUAL，REAL46-031 维持 DIFFERENT（基线不变）。

## 4. 结论与边界

- 冻结不变式全部通过；1556 全量闸门 **0 真实回归**（校正后 EQUAL 1180 /
  ERROR 376 逐案与基线一致，5 个抖动案 5/5 单案复跑归因闭环）；
  46 sweep **唯一变化 REAL46-019 DIFFERENT→EQUAL**，其余 44 案零变化；
  循环 header YIELD_VALUE 路径零产品漂移。**允许提交**。
- 如实登记：判官 R7 不递归类内 layer-2，REAL46-019 另有 3 个 co_code
  差异对判官不可见（`address_exclude` / `IPv4Network.__init__` /
  `IPv6Network.__init__`）；本轮未动判官、未按可见层凑整，019 转 EQUAL
  完全来自 v[19] 这一真实功能错误的修复。
- **不宣称 G1 / G2c / G3 / G4 / G6 通过；`product_complete` 仍 NOT PASS。**
  46 sweep 其余 10 DIFFERENT / 17 ERROR、pe8 while-1 重构族、na5、
  未领姊妹形态 ca6/ca13/ca15/cb5、REAL46-031 packaging.version 等均
  在下一轮挂账，未闭合。
