# G4 v3 分档：从未实测为真的规则，其锚点是否在 pycdc 的 live 调用链上

**状态：读数 + 分档证据，需评审；本文不宣称 G4 通过，也不把任何规则改判为 proved。**

输入全部只读：`fresh/gate_g4/universe_v3.json`、`traces_v3.json`、
`executed_inventory_v3.json`、`proof_records_v2.json`。`core/`、`scripts/`、`tests/`、
`rule_manifest.py`、`rule_universe.py`、`manifest_v2`/`universe_v2`/`traces_v2` 均未改动。

## 1. 口径（一个规则 = 一个 (kind, symbol) 组，平均 ~17 个锚点）

规则只要能**任一**锚点谓词为真就算命中，所以分档按**最优锚点**（最容易到达的那个）判定：

| 档 | 判据 |
|---|---|
| **D1 无 importer** | 该规则的**全部**锚点都落在「live 链上没有任何 importer」的模块里 ⇒ 结构上任何运行都到不了。 |
| **D2 类或函数从不构造/执行** | 没有任何锚点可达：某些锚点所在模块**在**链上（静态有 importer），但这些锚点所在的函数/方法/类体在 131 次 J 运行中**从未执行**，且该规则谓词**零次求值**。 |
| **D3 可达但无输入触发** | 至少一个锚点的所在函数执行过（或该规则谓词被求值过 ≥1 次），但谓词**从未实测为真** ⇒ J 的输入没驱动出该分支/该值。 |

live 链 = `pycdc.py`/`pycas.py` 的静态 import 闭包 ∪ 实测 pipeline 入口
（`core.cfg`、`core.cfg.region_ast_generator`、`core.cfg.ast_converter`、
`core.cfg.code_generator`）的静态 import 闭包。运行期核对用 `executed_inventory_v3.json`
（131 次运行 + import 阶段真实执行过的 code object）。

## 2. 总量

| 项 | 条数 |
|---|---|
| `empty_cov_true`（v3 谓词感知口径：131 次运行中从未实测为真） | **188** / 344 |
| D1 无 importer | **15** |
| D2 类或函数从不构造/执行 | **60** |
| D3 可达但无输入触发 | **113** |

按锚点模块聚合（同一规则可跨模块，这里按**代表锚点**的模块计）：

| 模块 | D1 | D2 | D3 | 合计 | 模块在链上 | 运行期执行过 |
|---|---|---|---|---|---|---|
| `core.cfg.region_ast_generator` | 0 | 5 | 41 | 46 | 是 | 是 |
| `core.cfg.ast_generator_v2` | 0 | 28 | 16 | 44 | 是 | 是 |
| `core.cfg.code_generator` | 0 | 16 | 26 | 42 | 是 | 是 |
| `core.cfg.comprehension_generator` | 0 | 0 | 14 | 14 | 是 | 是 |
| `core.cfg.objective_patch_detector` | 11 | 0 | 0 | 11 | 否 | 否 |
| `core.cfg.region_analyzer` | 0 | 2 | 9 | 11 | 是 | 是 |
| `core.cfg.structured_analyzer` | 0 | 7 | 0 | 7 | 是 | 是 |
| `core.cfg.pattern_parser` | 0 | 0 | 6 | 6 | 是 | 是 |
| `core.cfg.patch_detector` | 4 | 0 | 0 | 4 | 否 | 否 |
| `core.cfg.ast_converter` | 0 | 0 | 1 | 1 | 是 | 是 |
| `core.cfg.basic_block` | 0 | 1 | 0 | 1 | 是 | 是 |
| `core.cfg.exception_handler` | 0 | 1 | 0 | 1 | 是 | 否 |

## 3. D1：无 importer（锚点模块不在 live 调用链上）

证据：静态 import 图里这些模块的**链上 importer 为 0**，且 131 次运行**没有执行过**该模块的任何 code object（因此不是「执行了但没触发」，是「结构上不会被 import」）。

**15 条。** 前 10 条：

| rule_id | kind | symbol | 代表 anchor | scope | 锚点分布 D1/D2/D3 |
|---|---|---|---|---|---|
| `RULE-3d070d0913cc` | isinstance_ast | `If` | `core/cfg/objective_patch_detector.py:181` | `ObjectivePatchDetector._check_d2_special_branches` | 2/0/0 |
| `RULE-2b862ecf9a11` | isinstance_ast | `Compare` | `core/cfg/objective_patch_detector.py:191` | `ObjectivePatchDetector._extract_test_pattern` | 2/0/0 |
| `RULE-20568d2871b4` | isinstance_ast | `BoolOp` | `core/cfg/objective_patch_detector.py:195` | `ObjectivePatchDetector._extract_test_pattern` | 1/0/0 |
| `RULE-526c2f9c8010` | isinstance_ast | `Attribute` | `core/cfg/objective_patch_detector.py:197` | `ObjectivePatchDetector._extract_test_pattern` | 5/0/0 |
| `RULE-93efbfe2473b` | isinstance_ast | `Call` | `core/cfg/objective_patch_detector.py:199` | `ObjectivePatchDetector._extract_test_pattern` | 5/0/0 |
| `RULE-b56901a142a6` | isinstance_ast | `Name` | `core/cfg/objective_patch_detector.py:207` | `ObjectivePatchDetector._node_signature` | 3/0/0 |
| `RULE-fd29f404c20d` | isinstance_ast | `Subscript` | `core/cfg/objective_patch_detector.py:211` | `ObjectivePatchDetector._node_signature` | 1/0/0 |
| `RULE-1f3252f64295` | isinstance_ast | `Constant` | `core/cfg/objective_patch_detector.py:213` | `ObjectivePatchDetector._node_signature` | 1/0/0 |
| `RULE-2d4b43ea95f6` | isinstance_ast | `FunctionDef` | `core/cfg/objective_patch_detector.py:89` | `ObjectivePatchDetector.analyze_file` | 5/0/0 |
| `RULE-b3b3c27de3f4` | isinstance_ast | `AsyncFunctionDef` | `core/cfg/objective_patch_detector.py:89` | `ObjectivePatchDetector.analyze_file` | 3/0/0 |

模块级证据（importer 清单来自静态 AST 解析，扫描范围 `core/ parsers/ utils/ scripts/ tools/ tests/ pycdc.py pycas.py`）：

| 模块 | 链上 importer | 链外 importer | 运行期执行过 | 规则数 |
|---|---|---|---|---|
| `core.cfg.objective_patch_detector` | **（无）** | `scripts.phase6_final_test`、`scripts.run_baseline_detection` | 否 | 11 |
| `core.cfg.patch_detector` | **（无）** | （无） | 否 | 4 |

文本 grep 复核（`core/`、`parsers/`、`utils/`、`pycdc.py`、`pycas.py` 全部 .py，排除模块自身文件；只匹配到注释/文档字符串也算命中，所以「命中处不是 import」反而进一步说明没有 importer）：

| 模块 | 文本命中行数 | 命中样例 |
|---|---|---|
| `core.cfg.objective_patch_detector` | 0 | （0 处） |
| `core.cfg.patch_detector` | 2 | `core/cfg/patch_detector_enhanced.py:8`；`core/cfg/patch_detector_enhanced.py:704` |

## 4. D2：模块在链上，但类/函数从不构造、从不执行

证据：模块有链上 importer（表格里若 importer 是函数内 lazy import，还会标出该 import语句所在的函数在 131 次运行里是否真的跑过），但锚点所在函数/方法**一次都没执行**，且规则谓词**零次求值**。

**60 条。** 前 10 条：

| rule_id | kind | symbol | 代表 anchor | scope | 锚点分布 D1/D2/D3 |
|---|---|---|---|---|---|
| `RULE-5361acaaa053` | opcode_eq | `BINARY_FLOOR_DIVIDE` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 0/1/0 |
| `RULE-c7b3c96bb6c8` | opcode_eq | `BINARY_MODULO` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 0/1/0 |
| `RULE-dda45a0ced72` | opcode_eq | `BINARY_DIVIDE` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 0/7/0 |
| `RULE-05f8183d28bc` | opcode_eq | `GET_ATTR` | `core/cfg/ast_generator_v2.py:10653` | `ASTGeneratorV2._generate_if_ast` | 0/1/0 |
| `RULE-b611d12faec6` | opcode_eq | `PRINT_ITEM` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 0/2/0 |
| `RULE-beabfd586993` | opcode_eq | `PRINT_NEWLINE` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 0/2/0 |
| `RULE-d1e1d76ee83d` | opcode_eq | `PRINT_EXPR` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 0/2/0 |
| `RULE-bcde89ee3e2a` | opcode_eq | `BINARY_OR` | `core/cfg/ast_generator_v2.py:13181` | `ASTGeneratorV2._generate_if_ast` | 0/1/0 |
| `RULE-c56bc072e6e4` | opcode_eq | `BINARY_AND` | `core/cfg/ast_generator_v2.py:13181` | `ASTGeneratorV2._generate_if_ast` | 0/1/0 |
| `RULE-010c1b2cf1d7` | opcode_eq | `Break` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 0/2/0 |

类级核对（类是否**真的被构造**：静态实例化点是否落在实际执行过的代码里，以及 `<Class>.__init__` 是否真的跑过。注意：类被构造 ≠ 每个方法被调用——`CodeGenerator` 就被构造过，但它的 dict 分支 `_generate_dict_node` 从未被调用，所以那 16 条仍属 D2）：

| 类 | 文件 | 链上静态实例化/引用点 | 其中位于已执行代码 | 运行期 `__init__` 执行 | 该类的 D2 规则数 |
|---|---|---|---|---|---|
| `ASTGeneratorV2` | `core/cfg/ast_generator_v2.py` | 14 | 0 | **否** | 27 |
| `CodeGenerator` | `core/cfg/code_generator.py` | 11 | 2 | 是 | 16 |
| `StructuredAnalyzer` | `core/cfg/structured_analyzer.py` | 3 | 0 | **否** | 7 |
| `RegionASTGenerator` | `core/cfg/region_ast_generator.py` | 30 | 26 | 是 | 5 |
| `RegionAnalyzer` | `core/cfg/region_analyzer.py` | 6 | 4 | 是 | 2 |
| `BasicBlock` | `core/cfg/basic_block.py` | 735 | 497 | 是 | 1 |
| `ExpressionReconstructor` | `core/cfg/ast_generator_v2.py` | 21 | 3 | 是 | 1 |

函数级证据（scope 不在类里的 D2 规则）：

| rule_id | scope | 文件 | 链上引用 |
|---|---|---|---|
| `RULE-137de19b1304` | `_find_handler_type_load` | `core/cfg/exception_handler.py` | 1 |

完整清单（60 条）：

| rule_id | symbol | 代表 anchor | scope | 链上 importer | import 语句所在作用域是否跑过 |
|---|---|---|---|---|---|
| `RULE-5361acaaa053` | `BINARY_FLOOR_DIVIDE` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-c7b3c96bb6c8` | `BINARY_MODULO` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-dda45a0ced72` | `BINARY_DIVIDE` | `core/cfg/ast_generator_v2.py:10477` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-05f8183d28bc` | `GET_ATTR` | `core/cfg/ast_generator_v2.py:10653` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-b611d12faec6` | `PRINT_ITEM` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-beabfd586993` | `PRINT_NEWLINE` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-d1e1d76ee83d` | `PRINT_EXPR` | `core/cfg/ast_generator_v2.py:11556` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-bcde89ee3e2a` | `BINARY_OR` | `core/cfg/ast_generator_v2.py:13181` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-c56bc072e6e4` | `BINARY_AND` | `core/cfg/ast_generator_v2.py:13181` | `ASTGeneratorV2._generate_if_ast` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-010c1b2cf1d7` | `Break` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-6048d12971c9` | `While` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-681e794c6afb` | `For` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-6ce83d58fb8b` | `Continue` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-ae6695fa4fca` | `Match` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-cbb06f6eb54d` | `Try` | `core/cfg/ast_generator_v2.py:13459` | `ASTGeneratorV2._generate_if_ast.extract_elif_chain` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-5aba44e010fc` | `NOT` | `core/cfg/ast_generator_v2.py:17919` | `ASTGeneratorV2._generate_inner_while_from_block` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-85708f1fc4e5` | `SETUP_WITH` | `core/cfg/ast_generator_v2.py:21979` | `ASTGeneratorV2._extract_with_context` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-a310f7ea600b` | `PREP_RERAISE_STAR` | `core/cfg/ast_generator_v2.py:23481` | `ASTGeneratorV2._process_instruction_sequence` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-cdc6b865739a` | `FOR_ITER_RANGE` | `core/cfg/ast_generator_v2.py:26984` | `ASTGeneratorV2._extract_iterator_v2` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-8fc89ce420ac` | `_APPEND_OPS` | `core/cfg/ast_generator_v2.py:3330` | `ExpressionReconstructor._extract_comp_elt` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-0bc203be8823` | `Raise` | `core/cfg/ast_generator_v2.py:3954` | `ASTGeneratorV2._remove_unreachable_code` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-42045b244e8a` | `AsyncWith` | `core/cfg/ast_generator_v2.py:3965` | `ASTGeneratorV2._remove_unreachable_code` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-7ccfdf2f5d77` | `With` | `core/cfg/ast_generator_v2.py:3965` | `ASTGeneratorV2._remove_unreachable_code` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-1fbb15a6c511` | `If` | `core/cfg/ast_generator_v2.py:3992` | `ASTGeneratorV2._has_terminal_statement` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-b0bb824910b4` | `return` | `core/cfg/ast_generator_v2.py:4906` | `ASTGeneratorV2._extract_function_args` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-a758f665e9f5` | `DICT_ADD` | `core/cfg/ast_generator_v2.py:5966` | `ASTGeneratorV2._generate_comprehension_function` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-1c8e48e5d568` | `CALL_KW` | `core/cfg/ast_generator_v2.py:7387` | `ASTGeneratorV2._generate_block_content_skip_iterator` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-9ba093d040b1` | `YIELD` | `core/cfg/ast_generator_v2.py:8527` | `ASTGeneratorV2._generate_block_content_skip_iterator` | 8 | core.cfg@__init__.py:76(没跑)、core.cfg@__init__.py:208(没跑) |
| `RULE-60fc44ca8092` | `conditional_ops` | `core/cfg/basic_block.py:193` | `BasicBlock.is_conditional` | 12 | core.cfg@__init__.py:35(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:12(跑过) |
| `RULE-1f2bf6bdcd1e` | `Module` | `core/cfg/code_generator.py:262` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-0b22204ea11f` | `AsyncFor` | `core/cfg/code_generator.py:277` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-3b46d229d0af` | `AugAssign` | `core/cfg/code_generator.py:281` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-eed79a22277c` | `Assign` | `core/cfg/code_generator.py:283` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-eb29ec1ad01a` | `AnnAssign` | `core/cfg/code_generator.py:285` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-df8d199ebe90` | `Expr` | `core/cfg/code_generator.py:289` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-cc118c63f579` | `Pass` | `core/cfg/code_generator.py:318` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-8c816c79d0c7` | `Delete` | `core/cfg/code_generator.py:324` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-a99b10fa310d` | `Global` | `core/cfg/code_generator.py:326` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-3ed21c936d06` | `Nonlocal` | `core/cfg/code_generator.py:331` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-d712e20d2506` | `FunctionDef` | `core/cfg/code_generator.py:365` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-702b6dd6ca34` | `AsyncFunctionDef` | `core/cfg/code_generator.py:367` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-dff33ce626a7` | `ClassDef` | `core/cfg/code_generator.py:369` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-1b5b4d7115d9` | `Assert` | `core/cfg/code_generator.py:378` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-1601748f4b42` | `ImportFrom` | `core/cfg/code_generator.py:388` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-3c8a43d55e71` | `Import` | `core/cfg/code_generator.py:388` | `CodeGenerator._generate_dict_node` | 5 | core.cfg@__init__.py:196(没跑)、core.cfg@__init__.py:210(没跑) |
| `RULE-137de19b1304` | `_UNCOND_JUMP_TARGET_OPS` | `core/cfg/exception_handler.py:88` | `_find_handler_type_load` | 1 | core.cfg.structured_analyzer@structured_analyzer.py:11717(没跑) |
| `RULE-e950c889b956` | `_BIND_STORE_OPS` | `core/cfg/region_analyzer.py:16977` | `RegionAnalyzer._extract_with_items._parse_bind_unpack` | 3 | core.cfg@__init__.py:50(没跑)、core.cfg.comprehension_generator@comprehension_generator.py:4(跑过) |
| `RULE-a6c5590d7e93` | `_BIND_UNPACK_OPS` | `core/cfg/region_analyzer.py:16990` | `RegionAnalyzer._extract_with_items._parse_bind_unpack` | 3 | core.cfg@__init__.py:50(没跑)、core.cfg.comprehension_generator@comprehension_generator.py:4(跑过) |
| `RULE-31256e3fd90e` | `_STORE_OPS_R2P02` | `core/cfg/region_ast_generator.py:55933` | `RegionASTGenerator._build_ternary_boolop_condition` | 2 | core.cfg@__init__.py:61(没跑)、core.cfg@__init__.py:194(没跑) |
| `RULE-048e69dc7408` | `_v105_sub_attr` | `core/cfg/region_ast_generator.py:55935` | `RegionASTGenerator._build_ternary_boolop_condition` | 2 | core.cfg@__init__.py:61(没跑)、core.cfg@__init__.py:194(没跑) |
| `RULE-996e7c860ca0` | `_DELETE_NAME_OPS` | `core/cfg/region_ast_generator.py:65152` | `RegionASTGenerator._build_multi_target_del_targets` | 2 | core.cfg@__init__.py:61(没跑)、core.cfg@__init__.py:194(没跑) |
| `RULE-26ee397f261c` | `skip_ops` | `core/cfg/region_ast_generator.py:78406` | `RegionASTGenerator._generate_return_ast` | 2 | core.cfg@__init__.py:61(没跑)、core.cfg@__init__.py:194(没跑) |
| `RULE-5c5d7b71d2bb` | `_skip_ops` | `core/cfg/region_ast_generator.py:78461` | `RegionASTGenerator._generate_return_ast` | 2 | core.cfg@__init__.py:61(没跑)、core.cfg@__init__.py:194(没跑) |
| `RULE-36dde631fda0` | `SETUP_EXCEPT` | `core/cfg/structured_analyzer.py:13288` | `StructuredAnalyzer._identify_try_except_pre_311` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-36f063d106a0` | `SETUP_FINALLY` | `core/cfg/structured_analyzer.py:13288` | `StructuredAnalyzer._identify_try_except_pre_311` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-7f1501983cc4` | `DUP_TOP_TWO` | `core/cfg/structured_analyzer.py:13926` | `StructuredAnalyzer._identify_with_structures` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-a2f801d5aefb` | `ROT_THREE` | `core/cfg/structured_analyzer.py:13926` | `StructuredAnalyzer._identify_with_structures` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-c500ada1eadd` | `UNARY_OP` | `core/cfg/structured_analyzer.py:13926` | `StructuredAnalyzer._identify_with_structures` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-c708889ddc61` | `ROT_TWO` | `core/cfg/structured_analyzer.py:13926` | `StructuredAnalyzer._identify_with_structures` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |
| `RULE-fac0e268c522` | `DUP_TOP` | `core/cfg/structured_analyzer.py:13926` | `StructuredAnalyzer._identify_with_structures` | 3 | core.cfg@__init__.py:66(没跑)、core.cfg.ast_generator_v2@ast_generator_v2.py:14(跑过) |

## 5. D3：可达但无输入触发

证据：至少一个锚点所在函数执行过（或谓词被求值过），但**从未为真**——这是输入覆盖问题，不是 import 链问题。

**113 条。** 前 10 条：

| rule_id | kind | symbol | 代表 anchor | scope | 锚点分布 D1/D2/D3 |
|---|---|---|---|---|---|
| `RULE-4f466f58c93b` | opcode_eq | `Return` | `core/cfg/ast_converter.py:340` | `CFGASTConverter._convert_class_def` | 0/4/1 |
| `RULE-744e7a962f6d` | opcode_eq | `LOAD_CONSTANT` | `core/cfg/ast_generator_v2.py:1062` | `ExpressionReconstructor._process_instruction` | 0/3/2 |
| `RULE-b620fe7fb512` | opcode_eq | `LOAD_CLASSDEREF` | `core/cfg/ast_generator_v2.py:1103` | `ExpressionReconstructor._process_instruction` | 0/0/2 |
| `RULE-1c5bd7459d99` | opcode_eq | `POP_JUMP_BACKWARD_IF_NOT_NONE` | `core/cfg/ast_generator_v2.py:1372` | `ExpressionReconstructor._process_instruction` | 0/12/3 |
| `RULE-639e08245c2d` | opcode_eq | `POP_JUMP_BACKWARD_IF_NONE` | `core/cfg/ast_generator_v2.py:1410` | `ExpressionReconstructor._process_instruction` | 0/12/3 |
| `RULE-2c47b54ee0ba` | opcode_eq | `CALL_METHOD` | `core/cfg/ast_generator_v2.py:1512` | `ExpressionReconstructor._process_instruction` | 0/20/8 |
| `RULE-72af8df090f5` | opcode_eq | `CALL_FUNCTION` | `core/cfg/ast_generator_v2.py:1512` | `ExpressionReconstructor._process_instruction` | 0/26/7 |
| `RULE-b925e75b3739` | opcode_eq | `MAP_ADD` | `core/cfg/ast_generator_v2.py:1607` | `ExpressionReconstructor._process_instruction` | 0/6/5 |
| `RULE-f6348059bc55` | opcode_eq | `SET_UPDATE` | `core/cfg/ast_generator_v2.py:1655` | `ExpressionReconstructor._process_instruction` | 0/1/3 |
| `RULE-9e2d764f0456` | opcode_eq | `RETURN_CONST` | `core/cfg/ast_generator_v2.py:1877` | `ExpressionReconstructor._process_instruction` | 0/41/90 |

- 行到达、谓词恒假：**88** 条（J 已驱动到这一行，谓词每次都为假）
- 谓词零求值（分支未走到）：**25** 条（函数跑了，但这几行没到）

完整清单（113 条）：

| rule_id | symbol | 代表 anchor | scope | 求值次数 | 为真次数 |
|---|---|---|---|---|---|
| `RULE-4f466f58c93b` | `Return` | `core/cfg/ast_converter.py:340` | `CFGASTConverter._convert_class_def` | 244 | 0 |
| `RULE-744e7a962f6d` | `LOAD_CONSTANT` | `core/cfg/ast_generator_v2.py:1062` | `ExpressionReconstructor._process_instruction` | 49826 | 0 |
| `RULE-b620fe7fb512` | `LOAD_CLASSDEREF` | `core/cfg/ast_generator_v2.py:1103` | `ExpressionReconstructor._process_instruction` | 40758 | 0 |
| `RULE-1c5bd7459d99` | `POP_JUMP_BACKWARD_IF_NOT_NONE` | `core/cfg/ast_generator_v2.py:1372` | `ExpressionReconstructor._process_instruction` | 17497 | 0 |
| `RULE-639e08245c2d` | `POP_JUMP_BACKWARD_IF_NONE` | `core/cfg/ast_generator_v2.py:1410` | `ExpressionReconstructor._process_instruction` | 17440 | 0 |
| `RULE-2c47b54ee0ba` | `CALL_METHOD` | `core/cfg/ast_generator_v2.py:1512` | `ExpressionReconstructor._process_instruction` | 21873 | 0 |
| `RULE-72af8df090f5` | `CALL_FUNCTION` | `core/cfg/ast_generator_v2.py:1512` | `ExpressionReconstructor._process_instruction` | 18399 | 0 |
| `RULE-b925e75b3739` | `MAP_ADD` | `core/cfg/ast_generator_v2.py:1607` | `ExpressionReconstructor._process_instruction` | 16171 | 0 |
| `RULE-f6348059bc55` | `SET_UPDATE` | `core/cfg/ast_generator_v2.py:1655` | `ExpressionReconstructor._process_instruction` | 16144 | 0 |
| `RULE-9e2d764f0456` | `RETURN_CONST` | `core/cfg/ast_generator_v2.py:1877` | `ExpressionReconstructor._process_instruction` | 59342 | 0 |
| `RULE-75006c6546d1` | `RAISE` | `core/cfg/ast_generator_v2.py:2570` | `ExpressionReconstructor._process_instruction` | 3473 | 0 |
| `RULE-87685c80e83d` | `CACHE` | `core/cfg/ast_generator_v2.py:2666` | `ExpressionReconstructor._process_instruction` | 72749 | 0 |
| `RULE-90eafeab8219` | `MATCH_VALUE` | `core/cfg/ast_generator_v2.py:2890` | `ExpressionReconstructor._process_instruction` | 1584 | 0 |
| `RULE-cf0dd620521c` | `MATCH_MAPPING` | `core/cfg/ast_generator_v2.py:2917` | `ExpressionReconstructor._process_instruction` | 1867 | 0 |
| `RULE-9bedfd5ee85e` | `MATCH_KEYS` | `core/cfg/ast_generator_v2.py:2930` | `ExpressionReconstructor._process_instruction` | 1869 | 0 |
| `RULE-db1ffbe2c327` | `MATCH_AS` | `core/cfg/ast_generator_v2.py:2952` | `ExpressionReconstructor._process_instruction` | 1584 | 0 |
| `RULE-713e86bfd48b` | `MATCH_OR` | `core/cfg/ast_generator_v2.py:2967` | `ExpressionReconstructor._process_instruction` | 1584 | 0 |
| `RULE-0c6da108567a` | `<target>` | `core/cfg/code_generator.py:2116` | `CodeGenerator._generate_for_target` | 390 | 0 |
| `RULE-4773744d80c4` | `<lambda>` | `core/cfg/code_generator.py:2396` | `CodeGenerator._generate_function_def` | 934 | 0 |
| `RULE-33f06058607b` | `DictComp` | `core/cfg/code_generator.py:3780` | `CodeGenerator._generate_expression` | 213 | 0 |
| `RULE-2331b38d9765` | `ListComp` | `core/cfg/code_generator.py:3782` | `CodeGenerator._generate_expression` | 213 | 0 |
| `RULE-1ac0b3bb7543` | `SetComp` | `core/cfg/code_generator.py:3784` | `CodeGenerator._generate_expression` | 213 | 0 |
| `RULE-40c5ed4fe165` | `GeneratorExp` | `core/cfg/code_generator.py:3786` | `CodeGenerator._generate_expression` | 213 | 0 |
| `RULE-014265ded990` | `GenExpr` | `core/cfg/code_generator.py:3788` | `CodeGenerator._generate_expression` | 213 | 0 |
| `RULE-d46e58a97d98` | `Iter` | `core/cfg/code_generator.py:3790` | `CodeGenerator._generate_expression` | 211 | 0 |
| `RULE-bfbc22d0d1e3` | `Lambda` | `core/cfg/code_generator.py:3891` | `CodeGenerator._generate_expression` | 211 | 0 |
| `RULE-f1e6481a06fe` | `Subscript` | `core/cfg/code_generator.py:3910` | `CodeGenerator._generate_expression` | 191 | 0 |
| `RULE-1dc9e2f98754` | `Slice` | `core/cfg/code_generator.py:3930` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-823cae0aab30` | `JoinedStr` | `core/cfg/code_generator.py:3932` | `CodeGenerator._generate_expression` | 191 | 0 |
| `RULE-2e321a33507c` | `FormattedValue` | `core/cfg/code_generator.py:3935` | `CodeGenerator._generate_expression` | 191 | 0 |
| `RULE-d2b392e7ea86` | `BoolOp` | `core/cfg/code_generator.py:3960` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-09e890625a53` | `UnaryOp` | `core/cfg/code_generator.py:3963` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-e9cd9be060c0` | `Compare` | `core/cfg/code_generator.py:3966` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-84fd5ec5ec83` | `Await` | `core/cfg/code_generator.py:3969` | `CodeGenerator._generate_expression` | 187 | 0 |
| `RULE-3114624d4364` | `Yield` | `core/cfg/code_generator.py:3976` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-0453cb2cf048` | `YieldFrom` | `core/cfg/code_generator.py:3996` | `CodeGenerator._generate_expression` | 189 | 0 |
| `RULE-8637d89b4417` | `Attribute` | `core/cfg/code_generator.py:4032` | `CodeGenerator._generate_expression` | 2 | 0 |
| `RULE-4fb15b673728` | `Tuple` | `core/cfg/code_generator.py:4037` | `CodeGenerator._generate_expression` | 2 | 0 |
| `RULE-ec53116b4211` | `List` | `core/cfg/code_generator.py:4043` | `CodeGenerator._generate_expression` | 2 | 0 |
| `RULE-2ad1ffa97019` | `Set` | `core/cfg/code_generator.py:4047` | `CodeGenerator._generate_expression` | 2 | 0 |
| `RULE-7437333913d0` | `Dict` | `core/cfg/code_generator.py:4055` | `CodeGenerator._generate_expression` | 2 | 0 |
| `RULE-adbedd33701f` | `FunctionObject` | `core/cfg/code_generator.py:4085` | `CodeGenerator._generate_expression` | 0 | 0 |
| `RULE-938087af729e` | `__NESTED_FUNC__` | `core/cfg/code_generator.py:4115` | `CodeGenerator._generate_expression` | 14871 | 0 |
| `RULE-6cbf68b0c7ca` | `END_ASYNC_FOR` | `core/cfg/comprehension_generator.py:1262` | `ComprehensionGenerator._parse_comprehension_inner_impl` | 1900 | 0 |
| `RULE-9eea46812142` | `_jump_ops` | `core/cfg/comprehension_generator.py:1902` | `ComprehensionGenerator._value_chain_key_split_point` | 0 | 0 |
| `RULE-69b3129c2626` | `JUMP_ABSOLUTE` | `core/cfg/comprehension_generator.py:2078` | `ComprehensionGenerator._dict_shortcircuit_chain` | 30153 | 0 |
| `RULE-762ec4ca09c6` | `UNARY_NOT` | `core/cfg/comprehension_generator.py:2216` | `ComprehensionGenerator._get_stack_delta` | 66 | 0 |
| `RULE-b85ddfe6b1a8` | `UNARY_POSITIVE` | `core/cfg/comprehension_generator.py:2216` | `ComprehensionGenerator._get_stack_delta` | 66 | 0 |
| `RULE-da070a431a90` | `UNARY_NEGATIVE` | `core/cfg/comprehension_generator.py:2216` | `ComprehensionGenerator._get_stack_delta` | 66 | 0 |
| `RULE-4743f0da62f0` | `_b113_stop_ops` | `core/cfg/comprehension_generator.py:2379` | `ComprehensionGenerator._b113_extract_flat_clauses` | 88 | 0 |
| `RULE-6cc7b6a37fd5` | `SET_ADD` | `core/cfg/comprehension_generator.py:2488` | `ComprehensionGenerator._find_comp_append_op` | 41 | 0 |
| `RULE-54c66455c6d9` | `_cso` | `core/cfg/comprehension_generator.py:298` | `ComprehensionGenerator.try_generate_comprehension_assign` | 0 | 0 |
| `RULE-aca0cb9d01d5` | `_kop_names` | `core/cfg/comprehension_generator.py:3977` | `ComprehensionGenerator._b247_mixed_boolchain` | 187 | 0 |
| `RULE-d7cb17e16c13` | `_bounce_names` | `core/cfg/comprehension_generator.py:4064` | `ComprehensionGenerator._b247_mixed_boolchain` | 0 | 0 |
| `RULE-1576dfcf29af` | `_closure_setup` | `core/cfg/comprehension_generator.py:554` | `ComprehensionGenerator.try_generate_comprehension_assign` | 149 | 0 |
| `RULE-51cc986d9724` | `_pad` | `core/cfg/comprehension_generator.py:6219` | `ComprehensionGenerator._b271_dict_comp_kv` | 5 | 0 |
| `RULE-ba395f773988` | `_frame_bookkeeping` | `core/cfg/comprehension_generator.py:856` | `ComprehensionGenerator._find_returns_pending_value_successor` | 0 | 0 |
| `RULE-f9489f4c34b4` | `MATCH_MAPPING_KEYS` | `core/cfg/pattern_parser.py:2116` | `PatternParser._collect_pattern_bindings_from_successor` | 285 | 0 |
| `RULE-9a035d7e40e7` | `UNPACK_EXTRACT` | `core/cfg/pattern_parser.py:2190` | `PatternParser._extract_sequence_pattern` | 283 | 0 |
| `RULE-bf1c204659ed` | `POP_JUMP_IF_TRUE` | `core/cfg/pattern_parser.py:263` | `PatternParser._collect_pattern_blocks` | 3682 | 0 |
| `RULE-cb3db139681a` | `POP_JUMP_IF_FALSE` | `core/cfg/pattern_parser.py:263` | `PatternParser._collect_pattern_blocks` | 5246 | 0 |
| `RULE-f986afd96757` | `POP_JUMP_IF_NOT_NONE` | `core/cfg/pattern_parser.py:740` | `PatternParser._extract_case_guard_from_blocks._mr_guard_arm` | 1480 | 0 |
| `RULE-a6868eb8975c` | `POP_JUMP_IF_NONE` | `core/cfg/pattern_parser.py:748` | `PatternParser._extract_case_guard_from_blocks._mr_guard_arm` | 1418 | 0 |
| `RULE-8a6101820c9d` | `DELETE_GLOBAL` | `core/cfg/region_analyzer.py:23701` | `RegionAnalyzer._identify_conditional_regions` | 20463 | 0 |
| `RULE-efc4bb08d567` | `DELETE_NAME` | `core/cfg/region_analyzer.py:23701` | `RegionAnalyzer._identify_conditional_regions` | 20463 | 0 |
| `RULE-38d1a1fef6a0` | `DELETE_DEREF` | `core/cfg/region_analyzer.py:2463` | `RegionAnalyzer._detect_global_declarations` | 22581 | 0 |
| `RULE-6a468a10f3b9` | `SETUP_LOOP` | `core/cfg/region_analyzer.py:4663` | `RegionAnalyzer.identify_block_prefix_instructions` | 257 | 0 |
| `RULE-71f00ab8caf0` | `FORWARD_JUMP_IF_TRUE` | `core/cfg/region_analyzer.py:7160` | `RegionAnalyzer._is_while_true` | 979 | 0 |
| `RULE-90db7684358f` | `FORWARD_JUMP_IF_FALSE` | `core/cfg/region_analyzer.py:7160` | `RegionAnalyzer._is_while_true` | 979 | 0 |
| `RULE-b2e2ae122393` | `_NOISE` | `core/cfg/region_analyzer.py:8235` | `RegionAnalyzer._is_except_break_exit` | 0 | 0 |
| `RULE-18912491428c` | `POP_BLOCK` | `core/cfg/region_analyzer.py:8237` | `RegionAnalyzer._is_except_break_exit` | 0 | 0 |
| `RULE-a197991fd9e1` | `PURE_JUMP_OPS` | `core/cfg/region_analyzer.py:8246` | `RegionAnalyzer._is_except_break_exit` | 0 | 0 |
| `RULE-05ce2ee31a3b` | `IS_NOT` | `core/cfg/region_ast_generator.py:13577` | `RegionASTGenerator._loop_handle_header` | 0 | 0 |
| `RULE-1cd90d76c906` | `NOT_OP` | `core/cfg/region_ast_generator.py:13577` | `RegionASTGenerator._loop_handle_header` | 0 | 0 |
| `RULE-f3e459303717` | `_b33_noise` | `core/cfg/region_ast_generator.py:14671` | `RegionASTGenerator._b33_await_owner_merged_stmts` | 0 | 0 |
| `RULE-eea05924d17d` | `_cmp_ops_set` | `core/cfg/region_ast_generator.py:22142` | `RegionASTGenerator._try_build_ternary_operand_chained_compare` | 0 | 0 |
| `RULE-2397bb5fce28` | `JUMP_IF_FALSE` | `core/cfg/region_ast_generator.py:40616` | `RegionASTGenerator._generate_try` | 171 | 0 |
| `RULE-9d6678631130` | `JUMP_IF_TRUE` | `core/cfg/region_ast_generator.py:40616` | `RegionASTGenerator._generate_try` | 171 | 0 |
| `RULE-9890ff971e58` | `_CHECK_OPS_r08b` | `core/cfg/region_ast_generator.py:41678` | `RegionASTGenerator._generate_try` | 0 | 0 |
| `RULE-eb169da1a935` | `_hb_noise_ops` | `core/cfg/region_ast_generator.py:44096` | `RegionASTGenerator._generate_handler_body_statements` | 0 | 0 |
| `RULE-51fbefc39b4b` | `_ctx_value_ops` | `core/cfg/region_ast_generator.py:46427` | `RegionASTGenerator._b86_complete_with_items` | 0 | 0 |
| `RULE-097f2c50ba6b` | `UNARY_INVERT` | `core/cfg/region_ast_generator.py:51769` | `RegionASTGenerator._build_grouped_boolop_expression` | 65 | 0 |
| `RULE-a8dffc095ffd` | `attr` | `core/cfg/region_ast_generator.py:53295` | `RegionASTGenerator._build_boolop_augassign_target` | 0 | 0 |
| `RULE-e255ab564575` | `subscr` | `core/cfg/region_ast_generator.py:53329` | `RegionASTGenerator._build_boolop_augassign_target` | 0 | 0 |
| `RULE-e4932ccfc508` | `_b68_machinery` | `core/cfg/region_ast_generator.py:5399` | `RegionASTGenerator._b68_is_tryfin_tail_releasable` | 197 | 0 |
| `RULE-cd390e67679f` | `_STORE_CHK_R02` | `core/cfg/region_ast_generator.py:54367` | `RegionASTGenerator._generate_boolop_impl` | 0 | 0 |
| `RULE-4982a763071c` | `_STORE_CHK_P21` | `core/cfg/region_ast_generator.py:54561` | `RegionASTGenerator._generate_boolop_impl` | 7 | 0 |
| `RULE-d0e49b29cc07` | `_TRUE_POLARITY_COND_JUMP_OPS` | `core/cfg/region_ast_generator.py:56270` | `RegionASTGenerator._try_build_value_diamond_return` | 3 | 0 |
| `RULE-1ebd3fdc3786` | `_pre_store_ops` | `core/cfg/region_ast_generator.py:59014` | `RegionASTGenerator._generate_ternary` | 7 | 0 |
| `RULE-086b849c411a` | `CALL_FUNCTION_KW` | `core/cfg/region_ast_generator.py:6139` | `RegionASTGenerator._build_class_def` | 406 | 0 |
| `RULE-8b54bff8cdbb` | `_lit_skip_ops` | `core/cfg/region_ast_generator.py:73913` | `RegionASTGenerator._generate_block_statements_body` | 4 | 0 |
| `RULE-b6cb0f6833d9` | `_LITERAL_BUILD_OPS` | `core/cfg/region_ast_generator.py:73920` | `RegionASTGenerator._generate_block_statements_body` | 3 | 0 |
| `RULE-eb09655713ec` | `_WALRUS_INTEGRATING_OPS` | `core/cfg/region_ast_generator.py:73922` | `RegionASTGenerator._generate_block_statements_body` | 3 | 0 |
| `RULE-532506346aa4` | `_b107_store_ops` | `core/cfg/region_ast_generator.py:76387` | `RegionASTGenerator._build_chained_complex_target_assign` | 0 | 0 |
| `RULE-969c990c53ef` | `_mt_store_ops` | `core/cfg/region_ast_generator.py:76702` | `RegionASTGenerator._build_multi_target_unpack` | 0 | 0 |
| `RULE-1e9aca2acbea` | `INPLACE_ADD` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-2337ddef1650` | `INPLACE_POWER` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-262a0b01fd5d` | `INPLACE_RSHIFT` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-2f8806fa6f9b` | `INPLACE_MULTIPLY` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-3df67251fb10` | `INPLACE_MODULO` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-4cc164c4afcf` | `INPLACE_AND` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-8604910886cb` | `INPLACE_TRUE_DIVIDE` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-8a04c17a40dc` | `INPLACE_LSHIFT` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-8e5acd465385` | `INPLACE_OR` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-9432988e535a` | `INPLACE_FLOOR_DIVIDE` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-c911864da8dd` | `INPLACE_SUBTRACT` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-d88c60f60f49` | `INPLACE_XOR` | `core/cfg/region_ast_generator.py:77253` | `RegionASTGenerator._build_subscript_assign` | 1936 | 0 |
| `RULE-0062e270c4a1` | `BINARY_MULTIPLY` | `core/cfg/region_ast_generator.py:77389` | `RegionASTGenerator._build_subscript_assign` | 0 | 0 |
| `RULE-2675d342ef0c` | `BINARY_SUBTRACT` | `core/cfg/region_ast_generator.py:77389` | `RegionASTGenerator._build_subscript_assign` | 0 | 0 |
| `RULE-cd714078ea23` | `BINARY_ADD` | `core/cfg/region_ast_generator.py:77389` | `RegionASTGenerator._build_subscript_assign` | 0 | 0 |
| `RULE-f1bef410c01e` | `BINARY_TRUE_DIVIDE` | `core/cfg/region_ast_generator.py:77389` | `RegionASTGenerator._build_subscript_assign` | 0 | 0 |
| `RULE-e8aa239b163e` | `_yf_store_ops` | `core/cfg/region_ast_generator.py:7838` | `RegionASTGenerator._generate_loop` | 0 | 0 |
| `RULE-bed4750b6923` | `SETUP_ANNOTATIONS` | `core/cfg/region_ast_generator.py:940` | `RegionASTGenerator._extract_imports_from_block_prefix` | 685 | 0 |

## 6. 三类问题不能合并成一个数字

| 档 | 性质 | 修法 |
|---|---|---|
| D1 | 分母/结构 | 要么把这些模块显式排除出 G4 分母（并写明理由），要么让 pycdc 的 live 链真的 import 它 |
| D2 | 调用链/死代码 | 找到「本该调用它」的入口，或把死模块排除出分母 |
| D3 | 输入覆盖 | 增加 J 条目，把该分支/该值驱动出来 |

## 7. 复现

```powershell
# cwd = F:\Downloads\pythoncdc-main, 解释器 D:/Python/python.exe
D:/Python/python.exe -X utf8 fresh/gate_g4/trace_g4_v3.py `
  --universe fresh/gate_g4/universe_v3.json `
  --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json `
  --traces-v2 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/gate_gap/traces_v2.json `
  --out fresh/gate_g4/traces_v3.json --inventory-out fresh/gate_g4/executed_inventory_v3.json
D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4v2\triage_g4.py
```

## 8. 阅读注意

- 分档只解释**为什么没测到真谓词**，不评价规则对错；D3 之外的规则不是「坏规则」，
  而是「当前 J 打不到」。
- 本文档不改变任何规则的 `status`；`manifest_proved_v2.json` 里 open 仍是 open。
- 每档的「前 10 条」按 module/anchor 字典序取，不代表重要性排序。

