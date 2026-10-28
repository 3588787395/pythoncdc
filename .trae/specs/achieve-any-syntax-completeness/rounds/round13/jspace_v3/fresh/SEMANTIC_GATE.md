# Round13 全量语义回归闸门（1556 J 空间，rr-v5r80）

目的：Task 11（use_args 根因族）登记时判定「region 改动无干净全量语义闸门」。
本轮纠正该判断——**`semantic_runner` 用当前树 `pycdc.py` 重生成产品并跑语义差分**，
完整 1556 J 空间重跑**就是**全量语义回归闸门。本闸门同时确认 rr-v5r78 的 f-string
语法族修复在全量下**零语义回归**，并为后续 region 修复（Task 11.4）提供基线。

## 闸门机制

`tools/completeness/semantic_runner.py`（line 80）对每个条目执行
`[sys.executable, -X utf8, pycdc.py, <pyc>, -o <product>]`——即用**当前树**的
`pycdc.py`（走 core/cfg region + code_generator 路径）重新反编译生成产品，再由
`semantic_diff.py` 判 EQUAL/ERROR 等。故重跑当前树即检验当前 region/f-string 代码。

## 重跑（当前树 = post-B275 + rr-v5r78 f-string 修复）

对 `judgment_space_v3.json`（1556 条）三分片重生成产品 + 语义判定，与 post-B275
基线 `b275_regression/regress_shard{0,1,2}.json` 逐条比对（`compare_v5r79.py`）：

| 分片 | offset/limit | 新判决 | 基线 | 逐条变化 |
|---|---|---|---|---|
| shard0 | 0/519 | EQUAL 343 / ERROR 176 | 同 | **0** |
| shard1 | 519/519 | EQUAL 394 / ERROR 125 | 同 | **0** |
| shard2 | 1038/518 | EQUAL 395 / ERROR 123 | 同 | **0** |
| **base 合计** | 1556 | EQUAL 1132 / ERROR 424 | 同 | **0 回归 0 改善** |

三族见证（repair/async/module）当前树重跑：

| 族 | 条数 | 新判决 | 覆盖 |
|---|---|---|---|
| repair | 36 | **36/36 EQUAL** | covered_5tuple 1050→1086 |
| async | 62 | **62/62 EQUAL** | →1148 |
| module | 32 | **32/32 EQUAL** | →1180 |

## 官方 G1 读数（merge + coverage_checker，当前树）

`merge_evidence.py` 逐层合并 → `coverage_checker.py`：

```
[coverage] J_total=1556 covered_5tuple=1180 probe_only=0 unexecuted=0 n/a=0
           inconclusive=0 excluded=376 uncovered=376 coverage=75.84%
[coverage] GATE FAIL: uncovered=376 (covered_5tuple is the only numerator)
```

与 post-B275 基线 `COVERAGE_V3M_B275.md` **逐项一致**：covered **1180/1556**、
excluded **376**、coverage **75.84%**、G1 **FAIL**（376 条 Linux `.so` 环境阻断，不变）。

## 结论

1. **f-string 语法族修复（rr-v5r78）在全 1556 J 空间 + 三族见证下零语义回归**：
   1556 条逐条判决与基线完全相同（EQUAL 1132→1132），covered_5tuple 不变 1180。
   rr-v5r78 的窄改动（仅 f-string 定界/转义/回退）在整语料验证安全。
2. **全量语义回归闸门已建立**：今后任何 region/产品码改动，只需重跑本链并与本基线
   （`semantic_v3m_v5r79_merged.json`，SHA 见下）比对，即可判定语义回归。Task 11.4
   的 use_args region 修复因此可行：改后重跑，若 1556 逐条仍 0 回归 + REAL46-004
   改善，即证安全。
3. **G1 不变**：仍 `1180/1556`、376 excluded（环境阻断，非产品缺陷）、G1 FAIL。
   `product_complete` 仍 **NOT PASS**。未宣称任何门禁通过。

## 诚实边界

- 424 base ERROR / 376 final excluded 是既有**环境阻断**（Linux x86_64 `.so`
  `IQCommon.data.TickDataCache` 等 Windows 无法加载），非产品缺陷，与基线一致。
- 本闸门验证的是**语义等价**（EQUAL 口径），不改变任何门禁阈值或判据。

## 证据哈希（SHA256）

| 文件 | SHA256 |
|---|---|
| `semantic_shard0_v5r79.json` | `DF16983B455EECE0C7AA5287E12144E63C07A2FCE2DC51C549FC0BA40DCFEB08` |
| `semantic_shard1_v5r79.json` | `33B27D87DA83884EB734F9169504366380015FDBF7981397C9EEC0907AABDF02` |
| `semantic_shard2_v5r79.json` | `122E42E26898B9D29895CA1E5D0741B9D13E1810D10D23A6A73EC4213C1DA143` |
| `semantic_repair_v5r79.json` | `80F28EF290492282598B86ED434C65C08CFEFBF72275229368219D41DE20A64A` |
| `semantic_async_v5r79.json` | `ED7D8B1EFA20811B5BF56E0317B931C2A20F753B2B0222BAFDE9BB6D4A3EEE05` |
| `semantic_module_v5r79.json` | `28713D9CAA5889653B667AF33F719608326210AD2583CB256352E5959BBB496A` |
| `semantic_v3m_v5r79_merged.json` | `AD5D378162F4040ECBB75C37FE3E021763245AA4D27AB4D938EC585F64783C64` |
| `coverage_v3m_b275_v5r79.json` | `AAF793FAFF683C3745A9591581DB7387B1C79302A269CBB35CBCF87A66494406` |
| `COVERAGE_V3M_B275_V5R79.md` | `655D999C06E23F5F387A8A41AC8996604206846B7AFDB58A7F5E2E62D2DA6944` |

## 复现命令

```powershell
$f = '.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
# 三分片（当前树重生成产品）
python -X utf8 tools/completeness/semantic_runner.py --space $f/judgment_space_v3.json --out $f/semantic_shard0_v5r79.json --report $f/semantic_shard0_v5r79_report.json --product-dir $f/semantic_products/v5r79_shard0 --offset 0 --limit 519
python -X utf8 tools/completeness/semantic_runner.py --space $f/judgment_space_v3.json --out $f/semantic_shard1_v5r79.json --report $f/semantic_shard1_v5r79_report.json --product-dir $f/semantic_products/v5r79_shard1 --offset 519 --limit 519
python -X utf8 tools/completeness/semantic_runner.py --space $f/judgment_space_v3.json --out $f/semantic_shard2_v5r79.json --report $f/semantic_shard2_v5r79_report.json --product-dir $f/semantic_products/v5r79_shard2 --offset 1038 --limit 518
# 逐条比对基线
python -X utf8 $f/compare_v5r79.py
# 三族 + merge + coverage（见 fresh/README.md 步骤 4–6，文件名换 v5r79）
```
