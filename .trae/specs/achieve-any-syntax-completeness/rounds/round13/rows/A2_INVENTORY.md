# A2 删除批清查清单（HEAD=52128723 + A1 工作树）

日期：2026-11-26 ｜ 输出目录：`D:\temp\opencode\cl_layout\g4d\row4_stage2\`
依据：ROW4_RULE_COVERAGE.md 裁定③（(b)19 修死优先、删除次之、排除兜底）

## 1. `_generate_dict_node`（gdn）20 个调用点全清单

树外入口（2，删除对象 = 入口守卫）：
| # | 位置 | 形态 |
|---|------|------|
| 1 | `generate()` L133 | `if isinstance(node, dict): self._generate_dict_node(node); return ...`（L132-134） |
| 2 | `_generate_node()` L185 | 同上守卫（L182-186，含 2 行注释） |

梯子层内（18，全部随删除对象一起消失）：
| # | 调用方位置 |
|---|-----------|
| 3-4 | `_generate_dict_node` L268 / L301（自递归） |
| 5 | `_generate_function_def_dict_impl` L564 |
| 6 | `_generate_single_stmt_line` L716 |
| 7-15 | `_generate_try_dict` L736/740/752/756/813/832/844/862/874 |
| 16 | `_generate_with_dict` L924 |
| 17 | `_generate_assign_dict` L1118 |
| 18 | `_generate_class_def_dict` L2914 |
| 19-20 | `_generate_match_case_dict` L5678 / L5682 |

## 2. 删除集（code_generator.py，BOM+CRLF，6715 行）

方法 19 个（AST 精确行跨，合计 1079 行，见 a2_spans.json）：
| 方法 | 行跨 |
|------|------|
| `_generate_dict_node` | 255-466 |
| `_generate_aug_assign_dict`（重复定义之一） | 468-481 |
| `_generate_function_def_dict` | 483-520 |
| `_generate_function_def_dict_impl` | 522-573 |
| `_generate_single_stmt_line` | 712-720 |
| `_generate_try_dict` | 722-879 |
| `_generate_with_dict` | 881-929 |
| `_generate_delete_dict` | 931-957 |
| `_generate_if_dict` | 959-1036 |
| `_generate_elif_or_else_dict` | 1038-1083 |
| `_generate_return_dict` | 1085-1092 |
| `_generate_assign_dict` | 1094-1232 |
| `_generate_aug_assign_dict`（重复定义之二，遮蔽前者） | 1234-1252 |
| `_generate_ann_assign_dict` | 1254-1270 |
| `_generate_for_dict` | 1345-1397 |
| `_generate_while_dict` | 1399-1430 |
| `_generate_class_def_dict` | 2883-2919 |
| `_generate_slice_as_function_call`（唯一调用方 `_generate_assign_dict`@1113） | 4938-4988 |
| `_generate_match_case_dict` | 5646-5685 |

入口守卫 2 处 + FunctionObject 分支 1 处：
- `generate()` L132-135（isinstance 守卫 + 空行）
- `_generate_node()` L182-187（注释 2 行 + isinstance 守卫 + 尾随空行）
- `_generate_expression` FunctionObject elif L4085-4101（RULE-adbedd33701f；不在 gdn 内，是 dict 路径 node_type 链的独立分支；L4102 注释与 L4103 annotation 兜底保留）

basic_block.py（无 BOM、全 LF、375 行）：
- `is_conditional` L174-196（RULE-60fc44ca8092）

## 3. 保留集（dict 层存活子路径——有活调用方，一律不动）

| 方法 | 活调用方（节选） |
|------|------------------|
| `_generate_annotation_from_dict` | `_generate_function_def_impl`@2451、`_generate_class_def`@2844、`_generate_expression`@4103、`_generate_arguments`@6521/6570/6643 等 10 处 |
| `_generate_arguments_dict` | `_generate_lambda_expr`@6106、`_generate_lambda_from_dict`@5610 |
| `_generate_for_target_from_dict` | `_generate_comprehensions`@6145 |
| `_generate_gen_expr_from_dict` | `_generate_expression`@3787/3789/3864、`_generate_list_comp`@5517 |
| `_generate_list_comp_from_dict` / `_generate_set_comp_from_dict` | `_generate_expression`@3783/3785、`_generate_list_comp`@5511/5513 |
| `_generate_binop/_boolop/_compare/_ifexp/_unaryop/_joined_str/_formatted_value/_slice/_lambda_from_dict` | dict 路径 3783-4103 保留区 |
| `_get_dict_expr_precedence`、`_extract_fstring_pieces_from_dict`、`_formatted_value_pieces_from_dict`、`_generate_format_spec_inner_from_dict`、`_generate_comprehensions_from_dict` | 保留区内互调 |

## 4. 生产链路调用方核实（全部先转换，无一裸传 dict）

- pycdc.py L88-100（region 路径）：`CFGASTConverter().convert(ast_dict)` → `generate(py_ast)` ✓
- parsers/unified_generator.py L101-111：同构 ✓
- tools/completeness/rule_proof_check.py@799/810、_r7_g4_trace.py@52、fresh/gate_g4/trace_g4_v3.py@257、tests/test_functional_verification.py@198-202、tests/helpers/decompilation_helper.py@116-120 ✓
- tools/completeness/jspace_generator.py:1325 = NEW_REASONS["ExceptStar"] 文档字符串，全文件零 CFGCodeGenerator/CodeGenerator 引用 → 非调用方 ✓

## 5. 裸传 dict 的测试调用方（删除须同步对齐，共 14 文件 17 处）

| 文件 | 位置 | 处置 |
|------|------|------|
| tests/completeness/test_l1_basic_structures.py | L11 | 插入 CFGASTConverter 转换 |
| tests/completeness/test_l2_nested.py | L17-18 | 同上 |
| tests/completeness/test_l3_deep_nested.py | L30-31 | 同上 |
| tests/completeness/test_l4_extreme_nested.py | L19-20 | 同上 |
| tests/control_flow_matrix/base.py | L100-104 | 同上 |
| tests/control_flow_matrix/test_region_decoupling.py | L27-28 | 同上 |
| tests/control_flow_completeness/base.py | L25-36（双分支） | 同上 |
| tests/iteration/decompile_tester.py | L21-24、L46-52 | 同上 |
| tests/iteration/regions/round_driver.py | L32-34 | 同上 |
| tests/test_ternary_combinations.py | L58-68 | 同上 |
| tests/run_all_tests.py | L55-59 | 同上 |
| tests/nook/test_regression.py | L31-34、L144-147 | 同上（硬编码 d:\Desktop 路径，本为休眠态） |

is_conditional 测试调用方（2 处，随方法删除）：
| 文件 | 位置 | 处置 |
|------|------|------|
| tests/nook/test_regression_cfg.py | L30 | 删除该断言行 |
| tests/nook/test_cfg.py | L76-82 | 删除 test_is_conditional 整个方法 |

## 6. 删除前基线（HEAD+A1 工作树实测）

- tests/completeness/test_l1_basic_structures：52 项 = 29 过 / 5 败 / 18 错（经 dict 梯子）
- test_l2_nested：40 项 = 26 过 / 1 败 / 13 错
- test_l3_deep_nested：18 项 = 13 过 / 5 错
- test_l4_extreme_nested：5 项 = 4 过 / 1 错
- test_region_decoupling：40 项 = 24 过 / 5 败 / 11 跳
- test_ternary_combinations：非 unittest（脚本，0 项发现）
- 结论：dict 梯子**生产死、测试活**（约 96 项经梯子通过）；删除+测试对齐后按转换路径复测记录。

## 7. 顺带发现（未裁决，仅报告，不动）

- `_generate_dict_comp_from_dict`（L5687-）：全仓零调用方，属先在死代码；不在 (b)19 裁定内 → 保留原样，报告。
- `_generate_aug_assign_dict` 双定义（L468 与 L1234，后者遮蔽前者）——两处均仅被删除集调用，随删除集一并消失。
- code_generator.py 内多处注释提及被删方法名（如 L3978 注释提 `_generate_dict_node`）→ 留存（陈旧注释，非代码），避免额外行漂移。
- `generate()`/`_generate_expression` 的签名注解仍含 `Dict[str, Any]` → 留存（注解，非代码路径）。

## 8. 三案 census 设置（census_head / census_a1 / census_a2）

- 案一 tree_head = 干净 HEAD 52128723（agv2 与 git 对象字节一致，已校验）
- 案二 tree_a1 = HEAD + A1（与 tree_head 仅 agv2 一文件异 = A1 单行，已校验）
- 案三 = 工作树（HEAD+A1+A2，A2 应用后运行）
- 语料：a2_corpus.json 实数 **2510**（父方 2507 为旧口径；门控以 changed=0 为准）
- 口径：进程内 `pycdc.decompile_pyc(p)`（region 模式）、LF 规范化 sha256[:16] 大写、JSONL 断点续跑（a2_census_run.py）
