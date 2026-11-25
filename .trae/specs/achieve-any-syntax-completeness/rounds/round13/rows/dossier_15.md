# 工具路径 15 条证据排除 Dossier（no_occ (a) 类）

**范围**：proof_records_v8_b1.json 中 open reason=`no_occurrence_in_J` 且锚点位于
`core/cfg/patch_detector.py` / `core/cfg/objective_patch_detector.py` 的 15 条规则。

**结论**：15 条规则全部为**纯工具路径**——它们是「补丁检测器」（反作弊/客观性校验工具）自身的
扫描谓词，不属于反编译度量路径。G4 的 J 度量（131 pyc × region/legacy_v2 双管道）在结构上
不可能触发它们，`no_occurrence_in_J` 是**宇宙归类错误**，不是反编译覆盖缺口。

## 15 条规则清单

| # | rule_id | symbol | anchor | 谓词位置（源码） |
|---|---|---|---|---|
| 1 | RULE-d53ac6879d6a | Assign | patch_detector.py:328 | `if isinstance(node, ast.Assign):` |
| 2 | RULE-4c10258ace4e | List | patch_detector.py:425 | `elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):` |
| 3 | RULE-bd1b6b8bb350 | Set | patch_detector.py:425 | 同上 |
| 4 | RULE-87d3e450c5e4 | Tuple | patch_detector.py:425 | 同上 |
| 5 | RULE-2d4b43ea95f6 | FunctionDef | objective_patch_detector.py:89 | `if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):` |
| 6 | RULE-b3b3c27de3f4 | AsyncFunctionDef | objective_patch_detector.py:89 | 同上 |
| 7 | RULE-2845ddf0b9b8 | ClassDef | objective_patch_detector.py:93 | `if isinstance(node, ast.ClassDef):` |
| 8 | RULE-3d070d0913cc | If | objective_patch_detector.py:181 | `if isinstance(child, ast.If):` |
| 9 | RULE-2b862ecf9a11 | Compare | objective_patch_detector.py:191 | `if isinstance(test_node, ast.Compare):` |
| 10 | RULE-20568d2871b4 | BoolOp | objective_patch_detector.py:195 | `if isinstance(test_node, ast.BoolOp):` |
| 11 | RULE-526c2f9c8010 | Attribute | objective_patch_detector.py:197 | `if isinstance(test_node, ast.Attribute):` |
| 12 | RULE-93efbfe2473b | Call | objective_patch_detector.py:199 | `if isinstance(test_node, ast.Call):` |
| 13 | RULE-b56901a142a6 | Name | objective_patch_detector.py:207 | `if isinstance(node, ast.Name):` |
| 14 | RULE-fd29f404c20d | Subscript | objective_patch_detector.py:211 | `if isinstance(node, ast.Subscript):` |
| 15 | RULE-1f3252f64295 | Constant | objective_patch_detector.py:213 | `if isinstance(node, ast.Constant):` |

## 证据链（四重独立验证，均在 edc1ab08 shadow env）

**E1 静态 import 封闭（度量入口）**
G4 度量入口 `run_measurement`（`tools/completeness/rule_proof_check.py` L755-845）仅导入：
`core.cfg.build_cfg`、`core.cfg.region_ast_generator.RegionASTGenerator`、
`core.cfg.ast_converter.CFGASTConverter`、`core.cfg.code_generator.CFGCodeGenerator`、
`core.cfg.ast_generator_v2.generate_ast_v2`（L764-776）。两个检测器不在导入清单，
也不在上述 5 个模块的传递 import 闭包内。

**E2 静态引用封闭（core/ 内零调用方）**
全 core/ 范围内没有任何模块 import `patch_detector` 或 `objective_patch_detector`。
仓内引用方全部位于度量路径之外：`scripts/run_baseline_detection.py:20`、
`scripts/run_anti_patch_tests.py`、`scripts/phase6_final_test.py:7`、
`tools/completeness/jspace_generator.py:1325`（文档字符串提及）及 tests——
即它们只被「补丁检测基线脚本」调用，从不被反编译管道调用。

**E3 运行时探针（0 进入）**
`probe_runtime.py`（131 pyc × region + legacy_v2 双管道，与 v8_b1 同输入）：
两个文件的**所有函数 0 次进入**，15 条锚点行 0 次执行。探针与 v8_b1 的失败集完全一致
（m06/m08 legacy_v2），证明度量过程与 v8_b1 同构。

**E4 v8_b1 度量记录（0 谓词求值）**
v8_b1 中 15 条规则的 `predicate_evaluations=0`、`pyc_runs_reaching_site=0`、
`anchors_located` 均为正（宇宙扫描定位到了锚点），但运行期从未到达。

## 处置建议（供父会话裁决，不改宇宙）

- **排除**：将 15 条从 G4 规则覆盖分母中排除，归入「补丁检测器自有扫描宇宙」
  （universe_v6 应区分 decompiler-measurement 宇宙与 detector-tool 宇宙）。
- **验证方式**：若需独立复跑 E3/E4，用 `row4_noocc\v8b1_env` shadow env +
  `probe_runtime.py`（~4 分钟）或直接检查 v8_b1 的 rules[] 记录。
- **注意**：`objective_patch_detector` 的 11 条谓词（If/Compare/BoolOp/Attribute/Call/
  Name/Subscript/Constant/FunctionDef/AsyncFunctionDef/ClassDef）是 `_extract_test_pattern`
  / `_node_signature` 的 AST-isinstance 链——它们检测的是**检测目标模块的源码 AST**，
  与反编译器字节码处理谓词完全不同类，混入 G4 分母会使覆盖率统计失真。
