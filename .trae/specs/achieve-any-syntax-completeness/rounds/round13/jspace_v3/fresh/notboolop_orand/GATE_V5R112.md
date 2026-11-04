# rr-v5r112 全量回归闸门报告（GATE_V5R112）

生成：2026-11-05；Windows 11 Pro + git-bash；`export PATH="/usr/bin:/bin:$PATH"`；
Python `D:/Python/python.exe` 3.11.7。本轮只核验/落盘前序代理已完成的
`[v112-NOTBOOL]` 窄修复，不修改任何产品代码、判官、语料或探针输入。

## 1. 冻结不变式核验（实测，全部通过）

| 项 | 实测 |
|---|---|
| `scripts/pyc_verify.py` SHA256 | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` ✓ |
| `tools/completeness/semantic_diff.py` SHA256 | `DBCB1E246DD549F2C66A1D779F31EBA0506F9C99364DB02A679523DDE84D8174`（与 v5r111 基线 `judge_sha256` 逐字一致）✓ |
| `git diff -- tests/ scripts/pyc_verify.py tools/completeness/semantic_diff.py` | 空（0 行）✓ |
| `git status --short -- core parsers bytecode` | 仅 ` M core/cfg/region_ast_generator.py` ✓ |
| `git diff --numstat -- core/cfg/region_ast_generator.py` | `202 0`（+202 / -0；`[v112-NOTBOOL]` 标记 5 处）✓ |
| 三分片 + 46 sweep 的 `judge_sha256` | 全部 `dbcb1e246dd549f2c66a1d779f31eba0506f9c99364db02a679523dde84d8174`，与 v5r111 逐字一致 ✓ |

## 2. 闸门命令形态与落盘

在 repo 根执行，`--space` 用相对 repo 根路径，`--timeout 20`：

```
# 三分片（1556 条），路 A：shard0 → shard2
D:/Python/python.exe -X utf8 tools/completeness/semantic_runner.py \
  --space .../fresh/judgment_space_v3m_applied.json \
  --out .../fresh/semantic_shard{0,2}_v5r112.json --report ..._report.json \
  --product-dir D:/temp/opencode/cl_layout/r112gate/v112_shard{0,2} \
  --offset 0|1038 --limit 519|518 --timeout 20
# 路 B：shard1 → 46 sweep
D:/Python/python.exe -X utf8 tools/completeness/semantic_runner.py \
  --space .../fresh/judgment_space_v3m_applied.json \
  --out .../fresh/semantic_shard1_v5r112.json --report ..._report.json \
  --product-dir D:/temp/opencode/cl_layout/r112gate/v112_shard1 \
  --offset 519 --limit 519 --timeout 20
D:/Python/python.exe -X utf8 tools/completeness/semantic_runner.py \
  --space .trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json \
  --out .../fresh/notboolop_orand/semantic_46_v5r112.json --report ..._report.json \
  --product-dir D:/temp/opencode/cl_layout/r112gate/v112_g2c46 --timeout 20
```

落盘：三分片 `fresh/semantic_shard{0,1,2}_v5r112.json` + `_report.json`；
46 `fresh/notboolop_orand/semantic_46_v5r112.json` + `_report.json`。
逐案比对 `compare_v5r112.py` / `compare_v5r112_result.json`、单案复跑
`recheck_v5r112.py` / `recheck_v5r112_result.json` / `recheck_v5r112_final.json`
/`recheck_JS-WHILE-023_t120.json`、运行日志 `shard{0,1,2}.log` /
`g2c46.log` 全部按纪律写 `D:/temp/opencode/cl_layout/r112gate/`
（**中间产物不落证据目录、不入库**）；读数与逐案差异清单汇总于本文件。

### 环境适配（诚实记录，不改变判官输入）

1. **全新空 product-dir**：按纪律中间产物一律写
   `D:/temp/opencode/cl_layout/r112gate/`；三分片/46 sweep 各用独立全新空
   `v112_shard{0,1,2}` / `v112_g2c46`，规避 `decompile()` 对已存在产品
   `os.remove` 触发的本机 `SAFE_DELETE_BULK_CONFIRM_REQUIRED` 钩子
   （GATE_V5R111 第 2 节已登记）。`--product-dir` 只改变产品输出目录：
   本轮 `c3.product_path` 为 `D:\temp\...`（v5r111 为
   `fresh/semantic_products_v5r111/...`），而 `c4` verdict 由
   `semantic_diff.compare_case` 独立产生，与产品目录无关。
2. **2 路并行（与 v5r111 基线同并发度）**：本机 `os.cpu_count() = 2`；
   沿用 GATE_V5R111 最终策略——路 A：shard0 → shard2 串行，
   路 B：shard1 → 46 sweep 串行，各路独享 1 核，严格
   `--timeout 20`、`offset 0/519/1038` 与 `limit 519/519/518`，
   未合成、未回填。与基线相同并发度使抖动模式可比（基线 5 个 NO_C4
   抖动为同族 site-packages 大 pyc 反编译超时）。

## 3. 1556 J 空间三分片全量语义闸门

输入 `fresh/judgment_space_v3m_applied.json`（1556 条）。基线
`semantic_shard{0,1,2}_v5r111.json`：EQUAL 1180 / ERROR 371 / NO_C4 5
（对 v5r110 抖动校正后 EQUAL 1180 / ERROR 376）。

| 分片 | offset/limit | v5r111 基线 | v5r112 实测 | 逐案变化 |
|---|---|---|---|---|
| shard0 | 0 / 519 | EQUAL 367 / ERROR 150 + NO_C4 2 | EQUAL 367 / ERROR 151 + NO_C4 1 | 3（NO_C4↔ERROR） |
| shard1 | 519 / 519 | EQUAL 406 / ERROR 110 + NO_C4 3 | EQUAL 405 / INCONCLUSIVE 1 / ERROR 110 + NO_C4 3 | 7（1 EQUAL→INCONCLUSIVE + 6 NO_C4↔ERROR） |
| shard2 | 1038 / 518 | EQUAL 407 / ERROR 111 | EQUAL 407 / ERROR 111 | **0** |
| **合计** | 1556 | **EQUAL 1180 / ERROR 371 + NO_C4 5** | **EQUAL 1179 / INCONCLUSIVE 1 / ERROR 372 + NO_C4 4** | **10 抖动 / 0 实质回归** |

`compare_v5r112.py` 逐案比对（`compare_v5r112_result.json`）：三分片
**实质回归 0、改善 0、抖动 10**，shard2 逐案 0 变化；EQUAL 抖动校正后
1180 与基线逐案零变化。抖动归因校正后读数 **EQUAL 1180 / ERROR 376**，
与 v5r111 校正基线及 v5r110、v5r89 基线逐案一致。

## 4. 46 真实 pyc sweep

space `.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json`，
全量 46 条（不传 `--limit`）。基线
`fresh/orandchain_if/semantic_46_v5r111.json`：
12 DIFFERENT / 16 EQUAL / 17 ERROR + skip1。

| verdict | v5r111 | v5r112 |
|---|---|---|
| DIFFERENT | 12 | **11** |
| EQUAL | 16 | **17** |
| ERROR | 17 | 17 |
| skip（`c2_pyc_missing` = 已登记 REAL46-045） | 1 | 1 |
| NO_C4 | 0 | 0 |

逐案**唯一变化：REAL46-001 DIFFERENT → EQUAL**（本轮修复功效，
`D:\Python\Lib\dataclasses.py` 两叶 `co_consts.v[47]=_get_field` /
`v[69]=_process_class` 全消；`c4 = {verdict: EQUAL, diffs: [],
errors: [], inconclusive: []}`）；其余 **44 案 c4 verdict 逐案零变化**；
REAL46-004 / REAL46-036 维持 EQUAL。46 sweep 0 NO_C4、0 回归。
预期读数 **11 DIFFERENT / 17 EQUAL / 17 ERROR + skip1** 全中。

## 5. 抖动归因（历史纪律，10/10 单案复跑）

全部 10 个逐案变化以 `--offset <gidx> --limit 1` **单案无并发复跑**
（`recheck_v5r112.py`），落盘 `recheck_v5r112_result.json`；
`recheck_v5r112_final.json` 合并补跑后
`all_match(校正基线)=True / n=10`。校正基线：v5r111 的 5 个 NO_C4
是 GATE_V5R111 已登记并单案复跑证明的并发超时抖动，其稳定真值为
ERROR，故按 ERROR 比对（`all_match(原始基线)=False` 仅因此，非回归）。

| 案 | 分片 | gidx | v5r111 | v5r112 闸门 | 单案复跑 | 归因 |
|---|---|---|---|---|---|---|
| JS-AWAIT-008 | shard1 | 537 | EQUAL | INCONCLUSIVE | **EQUAL**（timeout 20） | `inconclusive: ["original execution timed out"]`，并发原件执行超时；无并发复跑 = EQUAL 与基线逐字一致 |
| JS-BOOLOP-011 | shard0 | 128 | ERROR | NO_C4 | **ERROR**（timeout 20） | `decompile_failed / TimeoutExpired` 大 pyc 反编译超时 |
| JS-CONTINUE-026 | shard1 | 869 | NO_C4 | ERROR | **ERROR**（timeout 20） | 基线 NO_C4 为已登记抖动，本轮恢复正常 ERROR（与校正基线逐字一致） |
| JS-CONTINUE-035 | shard1 | 878 | NO_C4 | ERROR | **ERROR**（timeout 20） | 同上 |
| JS-IF-075 | shard0 | 74 | NO_C4 | ERROR | **ERROR**（timeout 20） | 同上（GATE_V5R111 抖动案） |
| JS-TRY-103 | shard0 | 333 | NO_C4 | ERROR | **ERROR**（timeout 20） | 同上（GATE_V5R111 抖动案） |
| JS-WHILE-023 | shard1 | 901 | ERROR | NO_C4 | NO_C4（timeout 20）→ **ERROR（timeout 120）** | 212KB `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`，`--timeout 20` 边界 `TimeoutExpired`；加大 `--timeout 120` 单案无并发复跑 = ERROR（`errors: ["original artifact did not load/execute"]`），与基线逐字一致（`recheck_JS-WHILE-023_t120.json`） |
| JS-WHILE-037 | shard1 | 915 | NO_C4 | ERROR | **ERROR**（timeout 20） | 同 3（GATE_V5R111 抖动案） |
| JS-WITH-016 | shard1 | 684 | ERROR | NO_C4 | **ERROR**（timeout 20） | `TimeoutExpired` 大 pyc 反编译超时 |
| JS-WITH-083 | shard1 | 751 | ERROR | NO_C4 | **ERROR**（timeout 20） | `TimeoutExpired` 大 pyc 反编译超时 |

v5r111 基线 5 个 NO_C4（JS-IF-075 / JS-TRY-103 / JS-CONTINUE-026 /
JS-CONTINUE-035 / JS-WHILE-037）本轮全部恢复 ERROR；v5r112 新增
4 个 NO_C4（JS-BOOLOP-011 / JS-WHILE-023 / JS-WITH-016 / JS-WITH-083）
均为 `--timeout 20` 边界抖动，其中 JS-WHILE-023 需加大 timeout 才复现
稳定 ERROR。**无 JS-IF-074 / JS-WHILE-045 类 `None ↔ ERROR` 抖动，
无产品语义回归**；不回填分片文件。

## 6. 前序代理证据复核（只读）

- **复现矩阵 15 案全 BYTE-EQUAL**（`matrix_v5r112.py` / `matrix_v5r112_result.json`）：
  5 功效案（m4_not / m5_hash / m8_getfield / n8_not_or_and / n8_notnot）
  A/B TEXT-DIFF，10 控制案 TEXT-SAME。
- **A/B 回归电池 199 案**（`r112_regress.py` / `r112_regress_result.txt` / `.json`）：
  TEXT-DIFF 6（5 功效案 + `v111_prefix_stmts` 同族旧案一并修好，
  对源码 BYTE-EQUAL）/ 193 TEXT-SAME；10 个登记差全部 SAME-SIGNATURE；
  中间产物写 `D:/temp/opencode/cl_layout/r112regress/`。
- **权威 `semantic_diff.compare_case` 5 案**（`sd_v112_all.py` /
  `semantic_v112_all.json`）：REAL46-001 / 004 / 036 均
  **EQUAL（diffs=[]）**；REAL46-019（DIFFERENT，1 diff `v[19].code_sha`）、
  REAL46-031（DIFFERENT，2 diff `co_code.len` / `co_code.sha256`）
  与修复前基线 `status + diffs` 全签名一致 = BASELINE-UNCHANGED。
- **pytest 7 套件**（`pytest_v5r112.log`）：`3 failed / 277 passed /
  2 xpassed`，3 个 failed 与基线逐名一致——2 个冻结对
  （`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function`）+ 第 3 个
  `TestProductFreshness::test_products_match_current_code`（在位
  site-packages 产物预存在陈旧，历史已 A/B 实证非本轮引入），
  **零新增失败**。
- 修复：`core/cfg/region_ast_generator.py` +202/-0 只增不破，
  `[v112-NOTBOOL]` 5 处标记；新增 `_v112_broken_or_true_exit_exprs()` /
  `_v112_fixup_if_node()` + 值链 UNARY_NOT 汇合块归位 + 2 处出口调用；
  `region_analyzer.py` 零改动（详见 `FINDING.md` / `fix_patch_v5r112.diff`）。

## 7. 结论

- 1556 三分片闸门 **0 实质回归**（抖动校正后 EQUAL 1180 / ERROR 376
  逐案与基线一致；10 个抖动案 10/10 单案复跑归因完成）；46 sweep
  **唯一变化 REAL46-001 DIFFERENT→EQUAL**，其余 44 案零变化。
- 冻结不变式全通过；比较器与 `tests/` 零改动；可提交。
- **不宣称 G1 / G2c / G3 / G4 / G6 通过；`product_complete` 仍 NOT PASS。**
  46 sweep 其余 11 DIFFERENT / 17 ERROR 维持登记；下一轮家族见
  `tasks.md` Task 38 剩余登记。

## 8. 证据哈希与提交结构（如实记录）

| 文件 | SHA256 |
|---|---|
| `semantic_shard0_v5r112.json` | `6A3B71132C5034E3FD09D9550C4FD37A191495FF394242046DE3182E5F98B279` |
| `semantic_shard0_v5r112_report.json` | `B8AA7FD864D9FD1D82CFBA97A2DFB54FFDCAB2460971A5ED1CF81AC26DCBC6DB` |
| `semantic_shard1_v5r112.json` | `EAD9819F0A770F2A60E3868374DF04FE575709683CE2DD0DB39592746F66869B` |
| `semantic_shard1_v5r112_report.json` | `93A24282037F30AEACE6F158EDACF36277DA06C079AC9121EFCDF2A0CBDFC526` |
| `semantic_shard2_v5r112.json` | `B78D31ABAF1B456085C7DCDA6D968C864E4A362AB44A961835D48EC2BF39B85E` |
| `semantic_shard2_v5r112_report.json` | `D943345DF19D0E7DE6A56BB262C74CD73F4B08D28A2BD263D607B0EEB51632BC` |
| `notboolop_orand/semantic_46_v5r112.json` | `97CE0D44C5BEC68ACA86BF2C88695AC481181D84E3DC17E6C91CD390DC208406` |
| `notboolop_orand/semantic_46_v5r112_report.json` | `7868448E63B312AC0E0E24B89CD87361232A7DA01B790EAA53A4015E339AE7B5` |

提交结构：`rr-v5r112:` 单个干净提交，按纪律**精确 `git add`**
（严禁 `git add -A` / `git add .`），文件为 1 源码 +
证据目录 41 个（38 现有 + 本轮 3 个：本文件、`semantic_46_v5r112.json`
+ report；3 个 `.pyc` + 1 个 `.log` 受 `.gitignore` 忽略）+
6 个三分片 json/report + 2 个 spec 文档，合计 **50 个文件**。
该数字经与用户确认按清单完整提交（原 ≤45 为数字估计偏差，
非中间产物回潮；上轮教训的 860 个回归电池中间产物未入库）。
本文件与台账随该提交入库，**不自指自身 commit hash，不预断 push 结果**；
`git push origin main` 的实际状态与 commit hash 见最终报告与
`tasks.md` Task 38 的留痕，失败如实记录、不 force。
