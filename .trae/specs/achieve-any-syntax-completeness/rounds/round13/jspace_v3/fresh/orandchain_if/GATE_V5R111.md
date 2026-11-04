# rr-v5r111 全量回归闸门报告（GATE_V5R111）

生成：2026-11-04；Windows 11 Pro + git-bash；`export PATH="/usr/bin:/bin:$PATH"`；
Python `D:/Python/python.exe` 3.11.7。本轮只核验/落盘前序代理已完成的
`[v111-ORAND]` 窄修复，不修改任何产品代码、判官、语料或探针输入。

## 1. 冻结不变式核验（实测，全部通过）

| 项 | 实测 |
|---|---|
| `scripts/pyc_verify.py` SHA256 | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` ✓ |
| `tools/completeness/semantic_diff.py` SHA256 | `dbcb1e246dd549f2c66a1d779f31eba0506f9c99364db02a679523dde84d8174`（与 v5r110 基线 `judge_sha256` 逐字一致）✓ |
| `git diff -- tests/ scripts/pyc_verify.py tools/completeness/semantic_diff.py` | 空 ✓ |
| `git status --short -- core parsers bytecode` | 仅 ` M core/cfg/region_ast_generator.py` ✓ |
| `git diff --numstat -- core/cfg/region_ast_generator.py` | `184 0`（+184 / -0；`[v111-ORAND]` 标记 6 处）✓ |

## 2. 闸门命令形态与落盘

在 repo 根执行，`--space` 用相对 repo 根路径，`--timeout 20`：

```
# 三分片（1556 条）
D:/Python/python.exe -X utf8 tools/completeness/semantic_runner.py \
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_applied.json \
  --out   .../fresh/semantic_shard{0,1,2}_v5r111.json --report ..._report.json \
  --offset 0|519|1038 --limit 519|519|518 --timeout 20
# 46 sweep（全量，不传 limit）
D:/Python/python.exe -X utf8 tools/completeness/semantic_runner.py \
  --space .trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json \
  --out .../fresh/orandchain_if/semantic_46_v5r111.json --report ..._report.json --timeout 20
```

落盘：三分片 `fresh/semantic_shard{0,1,2}_v5r111.json` + `_report.json`；
46 `fresh/orandchain_if/semantic_46_v5r111.json` + `_report.json`；
逐案比对 `compare_v5r111.py` / `compare_v5r111_result.json`；
抖动复跑 `recheck_v5r111.py` / `recheck_v5r111_result.json` /
`recheck_auto_*.json`；运行日志 `gate_2way{A,B}_v5r111.log`。
（三分片原始 json 按命令形态落在 `fresh/` 根；本轮提交按纪律只精确 add
指定文件，读数与逐案差异清单已完整汇总于本文件及
`compare_v5r111_result.json`。）

### 环境适配（诚实记录，不改变判官输入）

1. **safe-delete 钩子**：首次用默认 product-dir 时，runner 的
   `decompile()` 会对已存在的历史产品文件执行 `os.remove(product)`；
   本机 `SAFE_DELETE_BULK_CONFIRM_REQUIRED` 在累计 50 次删除时终止进程
   （4 个 runner 均 `EXIT=1`、无 out 产出，`gate_run_v5r111.log` 留痕）。
   改用**全新空 product-dir**（`semantic_products_v5r111/r3_*`，0 次删除）
   后正常。`--product-dir` 只改变产品输出目录；c4 verdict 由
   `semantic_diff.compare_case` 独立产生，与产品目录无关。
2. **2 核并发策略**：本机 `os.cpu_count() = 2`。首次 4 路并行
   （3 分片 + 46）CPU 竞争激烈，46 sweep 出现 6 个
   `TimeoutExpired` / `NO_C4`（REAL46-004/008/010/018/019/020），按纪律
   **弃用该结果**（`gate_46_v5r111.log` 留痕）。最终采用 **2 路并行**
   （路 A：shard0 + shard2；路 B：shard1 + 46），各路独享 1 核，严格
   `--timeout 20` 与 `offset 0/519/1038` 三分片，未合成、未回填。

## 3. 1556 J 空间三分片全量语义闸门

输入 `fresh/judgment_space_v3m_applied.json`（1556 条）。基线
`semantic_shard{0,1,2}_v5r110.json`：EQUAL 1180 / ERROR 376
（对更早 v5r89 基线 0 回归）。

| 分片 | offset/limit | v5r110 基线 | v5r111 实测 | 逐案变化 |
|---|---|---|---|---|
| shard0 | 0 / 519 | EQUAL 367 / ERROR 152 | EQUAL 367 / ERROR 150 / NO_C4 2 | 2（ERROR→NO_C4） |
| shard1 | 519 / 519 | EQUAL 406 / ERROR 113 | EQUAL 406 / ERROR 110 / NO_C4 3 | 3（ERROR→NO_C4） |
| shard2 | 1038 / 518 | EQUAL 407 / ERROR 111 | EQUAL 407 / ERROR 111 | 0 |
| **合计** | 1556 | **EQUAL 1180 / ERROR 376** | **EQUAL 1180 / ERROR 371 / NO_C4 5** | **5 抖动 / 0 实质回归** |

`compare_v5r111.py` 逐案比对（落盘 `compare_v5r111_result.json`）：
三分片回归 **0**、改善 0、超时抖动 5，**EQUAL 1180 逐案零变化**。
抖动归因校正后读数为 EQUAL 1180 / ERROR 376，与 v5r110 及 v5r89
基线逐案一致。

## 4. 46 真实 pyc sweep

space `.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json`，
全量 46 条（不传 `--limit`）。基线
`fresh/chainfor_foriter/semantic_46_v5r110.json`：
13 DIFFERENT / 15 EQUAL / 17 ERROR + skip1。

| verdict | v5r110 | v5r111 |
|---|---|---|
| DIFFERENT | 13 | **12** |
| EQUAL | 15 | **16** |
| ERROR | 17 | 17 |
| skip（`c2_pyc_missing` = 已登记 REAL46-045） | 1 | 1 |
| NO_C4 | 0 | 0 |

逐案**唯一变化：REAL46-036 DIFFERENT → EQUAL**（本轮修复功效，
`pandas.core.indexing.check_dict_or_set_indexers`）；其余 **44 案 c4
verdict 逐案零变化**；REAL46-004 维持 EQUAL。46 sweep 0 NO_C4、0 回归。

## 5. 抖动归因（历史纪律）

最终 2 路并行闸门出现 5 个 `NO_C4`，全部为
`decompile_failed / TimeoutExpired`（site-packages 大 pyc 在 2 核并行下
反编译超过 20s，判定未产出），基线 c4 verdict 均为 `ERROR`（既有
real-package 环境阻断案，非产品缺陷）：

| 案 | 分片 | 全局 index | 基线 | 单案复跑 | 一致 |
|---|---|---|---|---|---|
| JS-IF-075 | shard0 | 74 | ERROR | ERROR | ✓ |
| JS-TRY-103 | shard0 | 333 | ERROR | ERROR | ✓ |
| JS-CONTINUE-026 | shard1 | 869 | ERROR | ERROR | ✓ |
| JS-CONTINUE-035 | shard1 | 878 | ERROR | ERROR | ✓ |
| JS-WHILE-037 | shard1 | 915 | ERROR | ERROR | ✓ |

`recheck_v5r111.py` 对每案以 `--offset <index> --limit 1 --timeout 20`
**单独复跑（无并发）**，`all_match=True`（落盘
`recheck_v5r111_result.json` 与 `recheck_auto_*.json`）——逐字与基线一致，
按历史纪律登记为并发超时抖动、**非回归**；不回填分片文件。
无 JS-IF-074 / JS-WHILE-045 类 `None ↔ ERROR` 抖动。
4 路弃用结果的 6 个 NO_C4 案在最终 46 sweep 中均恢复基线 verdict
（46 逐案零变化、0 NO_C4），等价于复跑证明。

## 6. 前序代理证据复核（只读）

- 复现矩阵 **12 案全 BYTE-EQUAL**：功效案 4（m1_exact / m2_no_genexpr /
  m4_single_if / two_if_diffmsg）A/B TEXT-DIFF，控制案 8 TEXT-SAME。
- 3 个未领扩展形态 `or_and3` / `or3_and2` / `prefix_stmts`：v111 与 HEAD
  产品逐字节相同，HEAD 基线即 recompile DIFF，如实登记未闭合。
- A/B 回归电池 **184 案**：TEXT-DIFF 4（恰 4 功效案）/ 180 TEXT-SAME。
- 权威 `semantic_diff.compare_case`：**REAL46-036 整案 EQUAL（diffs=[]）**
  完成 DIFFERENT→EQUAL；**REAL46-004 EQUAL（diffs=[]）** 维持闭合
  （`semantic_REAL46-036-v111.json` / `semantic_REAL46-004-v111.json`、
  `sd_r111.py`）。
- pytest 7 套件：`3 failed / 277 passed / 2 xpassed`——2 个冻结对
  （`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function`）+ 第 3 failed
  `TestProductFreshness::test_products_match_current_code`（在位
  site-packages 产物预存在陈旧，历史已 A/B 实证非本轮引入），**零新增失败**。

## 7. 结论

- 1556 三分片闸门 **0 实质回归**（EQUAL 1180 不变；5 个并发超时抖动案
  单案复跑与基线逐字一致）；46 sweep **唯一变化 REAL46-036
  DIFFERENT→EQUAL**，其余 44 案零变化。
- 冻结不变式全通过；比较器与 `tests/` 零改动；可提交。
- **不宣称 G1 / G2c / G3 / G4 / G6 通过；`product_complete` 仍 NOT PASS。**
  46 sweep 其余 12 DIFFERENT / 17 ERROR 维持登记；下一轮家族见
  `tasks.md` Task 37 剩余登记。

## 8. 提交与 push 状态（如实记录）

- 本地提交：主提交 `41d88a26eab2d6d96398627c7d75a55c6532cc71`
  （代码 + 证据，860 文件 / +14971 行）、台账提交 `fc3e4591`
  （tasks.md Task 37 + checklist.md 勾选项，2 文件 / +8 行），
  以及本节所在的 push 状态记录提交。三次均以 `rr-v5r111:` 开头。
- `git push origin main` **三次尝试均失败，未使用 `--force`**：
  两次普通 push 报
  `schannel: server closed abruptly (missing close_notify)`，
  一次 `http.version=HTTP/1.1` 兼容重试报 `CONNECT tunnel failed,
  response 502`。`origin/main` 仍停在 `55b36b1a`（rr-v5r110）；
  本地 rr-v5r111 提交全部就位，待网络恢复后重推。
  **如实记录 remote 不可用；未强行 force、未改写任何已发布提交。**
