# Wiki Index

- [[overview|Project Overview]] — 当前知识库状态总览
- [[log]] — 变更日志

## Modules

每个白名单源文件一页的骨架页（\kind: module\）。

- [[bytecode---init--|bytecode/__init__.py]]
- [[bytecode-bytecode-ops|bytecode/bytecode_ops.py]]
- [[bytecode-exception-table|bytecode/exception_table.py]]
- [[bytecode-pyc-disasm|bytecode/pyc_disasm.py]]
- [[bytecode-python311-support|bytecode/python311_support.py]]
- [[bytecode-python312-plus|bytecode/python312_plus.py]]
- [[bytecode-python39-310-support|bytecode/python39_310_support.py]]
- [[bytecode-unified-analyzer|bytecode/unified_analyzer.py]]
- [[core---init--|core/__init__.py]]
- [[core-ast-nodes|core/ast_nodes.py]]
- [[core-astree|core/astree.py]]
- [[core-bytecode-matcher|core/bytecode_matcher.py]]
- [[core-cache-system|core/cache_system.py]]
- [[core-cfg---init--|core/cfg/__init__.py]]
- [[core-cfg-ast-converter|core/cfg/ast_converter.py]]
- [[core-cfg-ast-generator-v2|core/cfg/ast_generator_v2.py]]
- [[core-cfg-basic-block|core/cfg/basic_block.py]]
- [[core-cfg-cfg-builder|core/cfg/cfg_builder.py]]
- [[core-cfg-cfg-optimizer|core/cfg/cfg_optimizer.py]]
- [[core-cfg-cfg-visualizer|core/cfg/cfg_visualizer.py]]
- [[core-cfg-code-generator|core/cfg/code_generator.py]]
- [[core-cfg-comprehension-generator|core/cfg/comprehension_generator.py]]
- [[core-cfg-dominator-analyzer|core/cfg/dominator_analyzer.py]]
- [[core-cfg-exception-handler|core/cfg/exception_handler.py]]
- [[core-cfg-objective-patch-detector|core/cfg/objective_patch_detector.py]]
- [[core-cfg-opcode-feature-detector|core/cfg/opcode_feature_detector.py]]
- [[core-cfg-patch-detector-enhanced|core/cfg/patch_detector_enhanced.py]]
- [[core-cfg-patch-detector|core/cfg/patch_detector.py]]
- [[core-cfg-pattern-parser|core/cfg/pattern_parser.py]]
- [[core-cfg-peephole-patterns|core/cfg/peephole_patterns.py]]
- [[core-cfg-region-analyzer|core/cfg/region_analyzer.py]]
- [[core-cfg-region-ast-generator|core/cfg/region_ast_generator.py]]
- [[core-cfg-structured-analyzer|core/cfg/structured_analyzer.py]]
- [[core-config|core/config.py]]
- [[core-control-flow|core/control_flow.py]]
- [[core-fast-stack|core/fast_stack.py]]
- [[core-object-pool|core/object_pool.py]]
- [[core-pyc-loader-v2|core/pyc_loader_v2.py]]
- [[core-pyc-objects|core/pyc_objects.py]]
- [[core-pyc-stream|core/pyc_stream.py]]
- [[core-pycobject|core/PycObject.py]]
- [[parsers---init--|parsers/__init__.py]]
- [[parsers-ast-builder-cleaned|parsers/ast_builder_cleaned.py]]
- [[parsers-ast-builder-unified|parsers/ast_builder_unified.py]]
- [[parsers-ast-builder|parsers/ast_builder.py]]
- [[parsers-code-generator|parsers/code_generator.py]]
- [[parsers-context-manager|parsers/context_manager.py]]
- [[parsers-enhanced-class-handler|parsers/enhanced_class_handler.py]]
- [[parsers-enhanced-decorator-handler|parsers/enhanced_decorator_handler.py]]
- [[parsers-enhanced-error-recovery|parsers/enhanced_error_recovery.py]]
- [[parsers-unified-generator|parsers/unified_generator.py]]
- [[pycdas|pycdas.py]]
- [[pycdc|pycdc.py]]
- [[utils---init--|utils/__init__.py]]
- [[utils-bytecode-comparator-cfg|utils/bytecode_comparator_cfg.py]]
- [[utils-bytecode-comparator|utils/bytecode_comparator.py]]
- [[utils-bytecode-verifier|utils/bytecode_verifier.py]]
- [[utils-compiler-optimization-handler|utils/compiler_optimization_handler.py]]
- [[utils-enhanced-logging|utils/enhanced_logging.py]]
- [[utils-source-equivalence-checker|utils/source_equivalence_checker.py]]
- [[utils-stack|utils/stack.py]]（`kind: module`）。

## Classes

核心类页（`kind: class`）。

- [[bytecode-python311-support--python311-instruction-analyzer|Python311InstructionAnalyzer @ bytecode/python311_support.py]]
- [[bytecode-unified-analyzer--unified-bytecode-analyzer|UnifiedBytecodeAnalyzer @ bytecode/unified_analyzer.py]]
- [[core-ast-nodes--ast-binary|ASTBinary @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-block|ASTBlock @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-call|ASTCall @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-decorator-application|ASTDecoratorApplication @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-for|ASTFor @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-function-def|ASTFunctionDef @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-if-exp|ASTIfExp @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-if|ASTIf @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-node-list|ASTNodeList @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-node|ASTNode @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-store|ASTStore @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-try|ASTTry @ core/ast_nodes.py]]
- [[core-ast-nodes--ast-with|ASTWith @ core/ast_nodes.py]]
- [[core-ast-nodes--code-generator|CodeGenerator @ core/ast_nodes.py]]
- [[core-astree--ast-iter-block|ASTIterBlock @ core/astree.py]]
- [[core-bytecode-matcher--bytecode-matcher|BytecodeMatcher @ core/bytecode_matcher.py]]
- [[core-cache-system--performance-cache|PerformanceCache @ core/cache_system.py]]
- [[core-cfg-ast-converter--cfgast-converter|CFGASTConverter @ core/cfg/ast_converter.py]]
- [[core-cfg-ast-generator-v2--ast-generator-v2|ASTGeneratorV2 @ core/cfg/ast_generator_v2.py]]
- [[core-cfg-ast-generator-v2--expression-reconstructor|ExpressionReconstructor @ core/cfg/ast_generator_v2.py]]
- [[core-cfg-basic-block--basic-block|BasicBlock @ core/cfg/basic_block.py]]
- [[core-cfg-cfg-builder--cfg-builder|CFGBuilder @ core/cfg/cfg_builder.py]]
- [[core-cfg-cfg-builder--control-flow-graph|ControlFlowGraph @ core/cfg/cfg_builder.py]]
- [[core-cfg-code-generator--code-generator|CodeGenerator @ core/cfg/code_generator.py]]
- [[core-cfg-comprehension-generator--comprehension-generator|ComprehensionGenerator @ core/cfg/comprehension_generator.py]]
- [[core-cfg-dominator-analyzer--dominator-analyzer|DominatorAnalyzer @ core/cfg/dominator_analyzer.py]]
- [[core-cfg-dominator-analyzer--loop-analyzer|LoopAnalyzer @ core/cfg/dominator_analyzer.py]]
- [[core-cfg-objective-patch-detector--objective-patch-detector|ObjectivePatchDetector @ core/cfg/objective_patch_detector.py]]
- [[core-cfg-opcode-feature-detector--opcode-feature-detector|OpcodeFeatureDetector @ core/cfg/opcode_feature_detector.py]]
- [[core-cfg-patch-detector-enhanced--enhanced-patch-detector|EnhancedPatchDetector @ core/cfg/patch_detector_enhanced.py]]
- [[core-cfg-pattern-parser--pattern-parser|PatternParser @ core/cfg/pattern_parser.py]]
- [[core-cfg-peephole-patterns--peephole-pattern-library|PeepholePatternLibrary @ core/cfg/peephole_patterns.py]]
- [[core-cfg-region-analyzer--if-region|IfRegion @ core/cfg/region_analyzer.py]]
- [[core-cfg-region-analyzer--loop-region|LoopRegion @ core/cfg/region_analyzer.py]]
- [[core-cfg-region-analyzer--region-analyzer|RegionAnalyzer @ core/cfg/region_analyzer.py]]
- [[core-cfg-region-analyzer--region|Region @ core/cfg/region_analyzer.py]]
- [[core-cfg-region-analyzer--try-except-region|TryExceptRegion @ core/cfg/region_analyzer.py]]
- [[core-cfg-region-ast-generator--region-ast-generator|RegionASTGenerator @ core/cfg/region_ast_generator.py]]
- [[core-cfg-structured-analyzer--region-analyzer|RegionAnalyzer @ core/cfg/structured_analyzer.py]]
- [[core-cfg-structured-analyzer--structured-analyzer|StructuredAnalyzer @ core/cfg/structured_analyzer.py]]
- [[core-control-flow--control-flow-analyzer|ControlFlowAnalyzer @ core/control_flow.py]]
- [[core-fast-stack--debug-stack|DebugStack @ core/fast_stack.py]]
- [[core-fast-stack--fast-stack|FastStack @ core/fast_stack.py]]
- [[core-pyc-objects--pyc-code|PycCode @ core/pyc_objects.py]]
- [[core-pyc-objects--pyc-module|PycModule @ core/pyc_objects.py]]
- [[core-pyc-objects--pyc-object|PycObject @ core/pyc_objects.py]]
- [[core-pyc-objects--pyc-ref|PycRef @ core/pyc_objects.py]]
- [[core-pyc-objects--pyc-string|PycString @ core/pyc_objects.py]]
- [[core-pyc-stream--pyc-data|PycData @ core/pyc_stream.py]]
- [[core-pyc-stream--pyc-file|PycFile @ core/pyc_stream.py]]
- [[core-pycobject--pyc-object|PycObject @ core/PycObject.py]]
- [[core-pycobject--pyc-ref|PycRef @ core/PycObject.py]]
- [[parsers-ast-builder--ast-builder|ASTBuilder @ parsers/ast_builder.py]]
- [[parsers-ast-builder--control-flow-analyzer|ControlFlowAnalyzer @ parsers/ast_builder.py]]
- [[parsers-ast-builder--data-flow-analyzer|DataFlowAnalyzer @ parsers/ast_builder.py]]
- [[parsers-ast-builder-cleaned--ast-builder|ASTBuilder @ parsers/ast_builder_cleaned.py]]
- [[parsers-ast-builder-cleaned--control-flow-analyzer|ControlFlowAnalyzer @ parsers/ast_builder_cleaned.py]]
- [[parsers-ast-builder-cleaned--data-flow-analyzer|DataFlowAnalyzer @ parsers/ast_builder_cleaned.py]]
- [[parsers-ast-builder-unified--unified-ast-builder|UnifiedASTBuilder @ parsers/ast_builder_unified.py]]
- [[parsers-code-generator--code-generator|CodeGenerator @ parsers/code_generator.py]]
- [[parsers-context-manager--context-manager|ContextManager @ parsers/context_manager.py]]
- [[parsers-unified-generator--unified-ast-generator|UnifiedASTGenerator @ parsers/unified_generator.py]]
- [[utils-compiler-optimization-handler--compiler-optimization-handler|CompilerOptimizationHandler @ utils/compiler_optimization_handler.py]]
- [[utils-enhanced-logging--pycdc-logger|PycdcLogger @ utils/enhanced_logging.py]]
- [[utils-source-equivalence-checker--source-equivalence-checker|SourceEquivalenceChecker @ utils/source_equivalence_checker.py]]
- [[utils-stack--fast-stack|FastStack @ utils/stack.py]]

## Concepts

算法/结构概念页（`kind: concept`）。

- [[ast-generation-lineages]] — 三代 AST 生成谱系（region / v2 / 自包含 control_flow）
- [[region-reduction-stages]] — 区域归约七阶段模型（460 方法归属实测 + 构造/消费判定规则）
- [[region-reduction-internals]] — 算法内部机制（四条不变量、优先级流水线、类型映射表、4 类已知失效模式）
- [[duplicate-code-matrix]] — 重复代码矩阵（ast_builder 双胞胎 212 同体函数、零引用死副本）
- [[cfg-anatomy]] — 程序自身控制流图的全部分支点（60 模块 / 6,923 单元 / **60,933 分支点**，子分支 91.2%，最深支配深度 164 层 = ast_builder._process_instruction，复杂度集中于 5 模块 82.1%，**region_ast_generator 独占 30.1% 为最大分支巢**——旧读数 51,518 因 BOM bug 漏掉该模块，已纠正）
- [[branch-conditions]] — 分支判定条件库（逐条件跟踪 + 相似度比较：61,289 判定点，7 类判定点分类，结构归一化 Name→N/Constant→C，结构哈希同形簇 1,903 组，similar/dupes 查询——缺陷同形定位与定向回归集）
- [[decompile-invariant-completeness]] — **反编译迭代总纲：嵌套无感与语法完备**（唯一权威文档：C1/C2/C3 无感不变式+归纳论证、分母 128、三级判定、13 条误解清单、T1–T8 映射、128 形态逐形态台账、破口登记 B1a/B1b/B2/B3/B4、except* 纠正、迭代机制落地标记+复审六步+状态机、口径演变史 v1–v6、全部可用资源索引。当前（v6 终审）：路径 100% / 形式层完备 128/破口 0/零能力 0 ⇒ 100%；组合级对抗挂账 25 号未清零。旧标准页与台账页已并入转址）

## Hotspots

补丁标记聚类页（`kind: hotspot`）。

- [[patch-marker-hotspots]] — 补丁标记热点（10 个 patch_markers>100 模块 + 100 行窗口聚类）
- [[patch-semantic-clusters]] — 补丁标记语义聚类（9,098 → 16 类，每类泛化方向 + 模式页对照）

## Patterns

缺陷模式页（`kind: pattern`，症状 → 区域类型 → 边界判据 → 原则 → 修复锚点；修复前先查此区）。

- [[if-continue-sibling-loss]] — P-1 if-continue 兄弟丢失（R23）
- [[if-absorbs-loop-sibling]] — P-2 IF 吸收循环后兄弟语句（R24A）
- [[loop-absorbs-outer-condition]] — P-3 Loop 吸收外层条件 / while-boolop 链越界（R24B）
- [[elif-chain-tail-lifted]] — P-4 elif 链尾随语句外提 → JUMP_FORWARD 跳错目标 NameError（R25）
- [[and-chain-partial-split]] — P-5 and 复合条件部分拆分（R26，方案 B 统一不拆分）

## Entities

## Sources

## Queries

- [[hot-modules]] — 补丁密集模块（Dataview）查询
- [[complexity-dashboard]] — 复杂度仪表盘（补丁密度 / god class / 模式页三视角）

## Comparisons

## Synthesis
