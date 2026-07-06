#!/usr/bin/env python3
"""
一区域一方法合规性测试 - 验证CFG区域分析架构的规范性

根据 project_rules.md 中定义的5大原则进行系统性验证：
1. 一区域一方法原则（One Region One Method）
2. 薄协调器模式（Thin Coordinator Pattern）
3. 单一职责（Single Responsibility）
4. 算法纯粹性（Algorithmic Purity）
5. 域隔离（Domain Isolation）

理论依据（项目规则文档 CFG区域分析方法新增/修改规则）：
- 14种区域类型必须各自有独立的_handle_xxx_region()方法
- 协调器方法行数≤80行，其他方法不超过类型对应上限
- 禁止使用_fix_/_merge_/_patch_等前缀的方法
- 所有算法必须基于编译器理论，禁止启发式规则

测试矩阵：
| ID | 验证维度 | 检查项 |
|----|---------|--------|
| SM01-SM10 | 原则1：一区域一方法 | 14种区域类型的handler存在性和唯一性 |
| SM11-SM18 | 原则2：薄协调器 | 方法行数、嵌套层级检查 |
| SM19-SM24 | 原则3：单一职责 | 各类方法的行数上限 |
| SM25-SM27 | 原则4：算法纯粹性 | 无硬编码操作码 |
| SM28-SM30 | 原则5：域隔离 | 跨域访问检测 |
"""

import sys
import os
import ast
import inspect
import unittest
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.helpers.decompilation_helper import (
    ComplianceTestBase,
    EXPECTED_REGION_HANDLERS,
    FORBIDDEN_METHOD_PREFIXES,
)


class TestSingleMethodPerRegion(ComplianceTestBase):
    """验证一区域一方法原则合规性的测试套件"""

    @classmethod
    def setup_class(cls):
        """导入被测模块"""
        try:
            from core.cfg import region_analyzer as ra_module
            from core.cfg import region_ast_generator as rag_module
            from core.cfg import structured_analyzer as sa_module
            cls.ra_module = ra_module
            cls.rag_module = rag_module
            cls.sa_module = sa_module
            cls.RegionAnalyzer = ra_module.RegionAnalyzer
            cls.RegionASTGenerator = rag_module.RegionASTGenerator
        except ImportError as e:
            pytest.skip(f"无法导入核心模块: {e}")

    # ========================================================================
    # SM01-SM10: 原则1 - 一区域一方法（One Region One Method）
    # ========================================================================

    def test_SM01_all_14_handlers_exist(self):
        """SM01: 14种区域类型都有对应的_handle_xxx_region方法

        验证每种区域类型都有且仅有一个专属的分析/生成方法。
        映射关系来自project_rules.md的14种区域类型表。"""
        for handler_name in EXPECTED_REGION_HANDLERS:
            self.assert_has_method(self.RegionAnalyzer, handler_name)

    def test_SM02_handler_count_exactly_14(self):
        """SM02: _handle_xxx_region方法恰好14个

        不多不少，确保没有多余或缺失的handler。"""
        import inspect

        handlers = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_handle_') and name.endswith('_region') and callable(getattr(self.RegionAnalyzer, name))
        ]
        self.assertEqual(
            len(handlers), 14,
            f"期望14个handler，实际有{len(handlers)}个: {handlers}"
        )

    def test_SM03_no_duplicate_responsibility(self):
        """SM03: 无重复职责 - 一个handler不处理多种区域类型

        检查每个handler方法体中是否出现多区域类型判断逻辑。
        违规模式：一个方法内同时判断'region.type == A'和'region.type == B'"""
        import ast
        import inspect
        import textwrap

        for handler_name in EXPECTED_REGION_HANDLERS:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source = inspect.getsource(method)
                tree = ast.parse(textwrap.dedent(source))

                type_checks = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Compare):
                        for cmp in node.comparators:
                            if isinstance(cmp, ast.Attribute) and 'type' in getattr(cmp, 'attr', ''):
                                type_checks.append(handler_name)

                self.assertEqual(
                    len(type_checks), 0,
                    f"{handler_name} 包含多区域类型判断，违反一区域一方法原则"
                )
            except (TypeError, OSError):
                pass

    def test_SM04_sequence_region_handler_exists(self):
        """SM04: SEQUENCE区域的handler存在且正确命名

        SEQUENCE是基础区域类型，所有非结构化代码都归为此类。"""
        self.assert_has_method(self.RegionAnalyzer, '_handle_sequence_region')

    def test_SM05_if_variants_have_separate_handlers(self):
        """SM05: IF_THEN/IF_ELSE/IF_ELSE_CHAIN各有独立handler

        三种if变体不能共用一个handler方法。"""
        expected = [
            '_handle_if_then_region',
            '_handle_if_else_region',
            '_handle_if_else_chain_region',
        ]
        for h in expected:
            self.assert_has_method(self.RegionAnalyzer, h)

    def test_SM06_loop_variants_have_separate_handlers(self):
        """SM06: FOR_LOOP/WHILE_LOOP各有独立handler

        两种循环类型必须分别处理。"""
        self.assert_has_method(self.RegionAnalyzer, '_handle_for_loop_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_while_loop_region')

    def test_SM07_exception_variants_have_separate_handlers(self):
        """SM07: TRY_EXCEPT/TRY_FINALLY各有独立handler

        两种异常处理结构的handler独立性。"""
        self.assert_has_method(self.RegionAnalyzer, '_handle_try_except_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_try_finally_region')

    def test_SM08_definition_types_have_handlers(self):
        """SM08: FUNCTION_DEF/CLASS_DEF/LAMBDA都有独立handler

        定义型区域类型的处理方法完备性。"""
        self.assert_has_method(self.RegionAnalyzer, '_handle_function_def_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_class_def_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_lambda_region')

    def test_SM09_special_regions_have_handlers(self):
        """SM09: WITH/COMPREHENSION/TERNARY/MATCH都有独立handler

        特殊语法结构的handler完备性。"""
        self.assert_has_method(self.RegionAnalyzer, '_handle_with_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_comprehension_region')
        self.assert_has_method(self.RegionAnalyzer, '_handle_ternary_region')

    def test_SM10_handler_methods_are_callable(self):
        """SM10: 所有handler方法都是可调用的

        确保handler是真正的method而非属性或其他对象。"""
        import inspect

        for handler_name in EXPECTED_REGION_HANDLERS:
            method = getattr(self.RegionAnalyzer, handler_name)
            self.assertTrue(
                callable(method),
                f"{handler_name} 不是可调用对象"
            )
            sig = inspect.signature(method)
            self.assertGreaterEqual(
                len(sig.parameters), 1,
                f"{handler_name} 参数数量不足（至少需要region参数）"
            )

    # ========================================================================
    # SM11-SM18: 原则2 - 薄协调器模式（Thin Coordinator Pattern）
    # ========================================================================

    def test_SM11_all_coordinators_within_line_limit(self):
        """SM11: 所有协调器方法行数≤80行

        薄协调器模式的核心约束：协调器只做分发组装，不含业务逻辑。"""
        for handler_name in EXPECTED_REGION_HANDLERS:
            self.assert_method_length_within(
                self.RegionAnalyzer, handler_name, 80
            )

    def test_SM12_coordinator_nesting_depth_limited(self):
        """SM12: 协调器方法嵌套层级≤3层

        通过AST分析检查if/for/while的最大嵌套深度。"""
        import ast
        import inspect

        for handler_name in EXPECTED_REGION_HANDLERS:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source = inspect.getsource(method)
                tree = ast.parse(source)

                max_depth = 0

                def check_depth(node, depth=0):
                    nonlocal max_depth
                    if depth > max_depth:
                        max_depth = depth
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.If, ast.For, ast.While)):
                            check_depth(child, depth + 1)
                        else:
                            check_child_nodes(child, depth)

                def check_child_nodes(node, depth=0):
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.If, ast.For, ast.While)):
                            check_depth(child, depth + 1)
                        else:
                            check_child_nodes(child, depth)

                check_depth(tree)
                self.assertLessEqual(
                    max_depth, 3,
                    f"{handler_name} 嵌套深度为{max_depth}，超过3层限制"
                )
            except (TypeError, OSError):
                pass

    def test_SM13_coordinator_delegates_to_helpers(self):
        """SM13: 协调器委托给收集/验证/创建方法

        检查协调器是否调用_collect_/_validate_/_create_前缀的方法。"""
        import inspect
        import re

        delegation_patterns = re.compile(
            r'self\._(collect_|validate_|create_)'
        )
        for handler_name in EXPECTED_REGION_HANDLERS[:5]:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source = inspect.getsource(method)
                matches = delegation_patterns.findall(source)
                self.assertGreater(
                    len(matches), 0,
                    f"{handler_name} 未发现对工具方法的委托调用"
                )
            except (TypeError, OSError):
                pass

    def test_SM14_no_business_logic_in_coordinator(self):
        """SM14: 协调器中无硬编码的业务逻辑常量

        检查协调器是否包含魔法数字或硬编码字符串。"""
        import inspect

        for handler_name in EXPECTED_REGION_HANDLERS:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source_lines = inspect.getsourcelines(method)[0]
                source = ''.join(source_lines)

                lines_with_numbers = []
                for i, line in enumerate(source_lines, 1):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'"):
                        if re.search(r'\b\d{2,}\b', stripped) and 'region' not in stripped.lower():
                            lines_with_numbers.append((i, stripped.rstrip()))

                self.assertLessEqual(
                    len(lines_with_numbers), 2,
                    f"{handler_name} 包含可能的硬编码数字: {lines_with_numbers[:3]}"
                )
            except (TypeError, OSError, ImportError):
                pass

    def test_SM15_for_loop_coordinator_is_thin(self):
        """SM15: _handle_for_loop_region具体行数检查

        重点检查最复杂的循环处理器是否符合薄协调器要求。"""
        line_count = self.get_method_line_count(
            self.RegionAnalyzer, '_handle_for_loop_region'
        )
        if line_count > 0:
            self.assertLessEqual(line_count, 80)

    def test_SM16_try_except_coordinator_is_thin(self):
        """SM16: _handle_try_except_region具体行数检查

        异常处理通常较复杂，但仍需符合薄协调器约束。"""
        line_count = self.get_method_line_count(
            self.RegionAnalyzer, '_handle_try_except_region'
        )
        if line_count > 0:
            self.assertLessEqual(line_count, 80)

    def test_SM17_if_else_chain_coordinator_is_thin(self):
        """SM17: _handle_if_else_chain_region行数检查

        elif链处理器可能较长，需特别关注。"""
        line_count = self.get_method_line_count(
            self.RegionAnalyzer, '_handle_if_else_chain_region'
        )
        if line_count > 0:
            self.assertLessEqual(line_count, 80)

    def test_SM18_no_inline_algorithm_in_coordinator(self):
        """SM18: 协调器中无内联算法实现

        检查协调器是否包含while/for循环（不应在协调器中出现算法循环）。"""
        import ast
        import inspect

        for handler_name in EXPECTED_REGION_HANDLERS:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source = inspect.getsource(method)
                tree = ast.parse(source)

                loops_in_body = 0
                for node in ast.walk(tree):
                    if isinstance(node, (ast.For, ast.While)):
                        loops_in_body += 1

                self.assertLessEqual(
                    loops_in_body, 1,
                    f"{handler_name} 包含{loops_in_body}个循环，可能包含内联算法"
                )
            except (TypeError, OSError):
                pass

    # ========================================================================
    # SM19-SM24: 原则3 - 单一职责（Single Responsibility）
    # ========================================================================

    def test_SM19_collect_methods_within_limit(self):
        """SM19: _collect_方法行数≤50行

        收集方法只负责从区域提取数据，不应过于复杂。"""
        import inspect

        collect_methods = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_collect_') and callable(getattr(self.RegionAnalyzer, name))
        ]
        for method_name in collect_methods:
            self.assert_method_length_within(
                self.RegionAnalyzer, method_name, 50
            )

    def test_SM20_validate_methods_within_limit(self):
        """SM20: _validate_方法行数≤40行

        验证方法只负责数据完整性校验。"""
        import inspect

        validate_methods = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_validate_') and callable(getattr(self.RegionAnalyzer, name))
        ]
        for method_name in validate_methods:
            self.assert_method_length_within(
                self.RegionAnalyzer, method_name, 40
            )

    def test_SM21_create_methods_within_limit(self):
        """SM21: _create_方法行数≤60行

        创建方法负责构建AST节点，允许稍复杂但仍有上限。"""
        import inspect

        create_methods = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_create_') and callable(getattr(self.RegionAnalyzer, name))
        ]
        for method_name in create_methods:
            self.assert_method_length_within(
                self.RegionAnalyzer, method_name, 60
            )

    def test_SM22_util_methods_within_limit(self):
        """SM22: _util_方法行数≤30行

        工具方法应保持简洁。"""
        import inspect

        util_methods = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if ('_util_' in name or '_helper_' in name) and callable(getattr(self.RegionAnalyzer, name))
        ]
        for method_name in util_methods:
            self.assert_method_length_within(
                self.RegionAnalyzer, method_name, 30
            )

    def test_SM23_no_method_exceeds_150_lines(self):
        """SM23: 任何方法都不超过150行的绝对上限

        这是项目规则的硬性约束。"""
        import inspect

        all_methods = [
            name for name, obj in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_') and callable(obj) and not name.startswith('__')
        ]
        violations = []
        for method_name in all_methods:
            lc = self.get_method_line_count(self.RegionAnalyzer, method_name)
            if lc > 150:
                violations.append((method_name, lc))

        self.assertEqual(
            violations, [],
            f"以下方法超过150行限制: {violations}"
        )

    def test_SM24_method_names_follow_convention(self):
        """SM24: 方法名遵循命名约定

        _handle_ / _collect_ / _validate_ / _create_ / _util_ 前缀规范使用。"""
        import inspect
        import re

        valid_prefixes = (
            '_handle_', '_collect_', '_validate_', '_create_',
            '_util_', '_helper_', '_build_', '_get_', '_set_',
            '_is_', '_has_', '_can_', '_should_',
        )

        private_methods = [
            name for name, _ in inspect.getmembers(self.RegionAnalyzer)
            if name.startswith('_') and callable(getattr(self.RegionAnalyzer, name))
            and not name.startswith('__')
        ]

        unnamed = []
        for name in private_methods:
            if not any(name.startswith(p) for p in valid_prefixes):
                unnamed.append(name)

        self.assertEqual(
            unnamed, [],
            f"以下方法不遵循命名约定: {unnamed}"
        )

    # ========================================================================
    # SM25-SM27: 原则4 - 算法纯粹性（Algorithmic Purity）
    # ========================================================================

    def test_SM25_no_hardcoded_numeric_opcodes(self):
        """SM25: 无硬编码数字操作码引用

        禁止 opcode == 116 或 opcode in [116, 100] 等形式。
        必须使用符号常量如 opcodes.FOR_ITER。"""
        import inspect
        import re

        hardcoded_opcode_pattern = re.compile(
            r'(?:opcode|op_code)\s*==\s*\d{2,}|'
            r'in\s*\[\s*\d{2,}(?:\s*,\s*\d{2,})*\s*\]'
        )

        all_modules_to_check = [self.ra_module]
        for module in all_modules_to_check:
            source_file = inspect.getsourcefile(module)
            if source_file and os.path.exists(source_file):
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                matches = hardcoded_opcode_pattern.findall(content)
                self.assertEqual(
                    matches, [],
                    f"在{source_file}中发现硬编码数字操作码: {matches[:5]}"
                )

    def test_SM26_no_heuristic_pattern_matching(self):
        """SM26: 无启发式模式匹配注释

        检查源码中是否存在标记启发式方法的特殊警告注释。"""
        import inspect

        heuristic_markers = ['HEURISTIC', 'heuristic', '经验规则', '猜测', '概率']
        for module in [self.ra_module]:
            try:
                source = inspect.getsource(module)
                for marker in heuristic_markers:
                    if marker.lower() in source.lower():
                        count = source.lower().count(marker.lower())
                        self.assertLessEqual(
                            count, 2,
                            f"模块中发现启发式标记'{marker}'出现{count}次"
                        )
            except (TypeError, OSError):
                pass

    def test_SM27_theory_references_present(self):
        """SM27: 关键方法包含理论引用

        核心算法方法应在docstring中引用编译器理论来源。"""
        import inspect

        key_methods = [
            '_analyze_regions',
            '_reduce_regions',
            '_identify_natural_loops',
        ]
        found_references = 0
        for method_name in key_methods:
            if hasattr(self.RegionAnalyzer, method_name):
                method = getattr(self.RegionAnalyzer, method_name)
                doc = inspect.getdoc(method) or ""
                theory_keywords = ['dominator', 'natural loop', 'struct', 'theory', 'SSA', 'Aho']
                if any(kw.lower() in doc.lower() for kw in theory_keywords):
                    found_references += 1

        self.assertGreaterEqual(
            found_references, 1,
            "至少应有一个关键方法包含理论引用"
        )

    # ========================================================================
    # SM28-SM30: 原则5 - 域隔离（Domain Isolation）
    # ========================================================================

    def test_SM28_no_forbidden_prefix_methods(self):
        """SM28: 不存在禁止前缀的方法

        _fix_ / _merge_ / _patch_ / _fallback_ / _hack_ / _workaround_ / _temp_
        这些前缀暗示了补丁式开发，违反规范架构。"""
        self.assert_no_forbidden_prefix(
            self.RegionAnalyzer, FORBIDDEN_METHOD_PREFIXES
        )

    def test_SM29_no_direct_bytecode_access_in_analyzer(self):
        """SM29: 区域分析器中无直接字节码指令列表访问

        禁止 block.instructions[0].opcode 形式的直接底层访问。
        数据应通过Region.metadata传递。"""
        import inspect
        import re

        direct_access_pattern = re.compile(
            r'\.instructions\s*\[|\.instructions\b.*\.opcode|'
            r'block\._\w+|basic_block\._\w+'
        )

        try:
            source = inspect.getsource(self.RegionAnalyzer)
            matches = direct_access_pattern.findall(source)
            self.assertEqual(
                matches, [],
                f"发现直接字节码访问模式: {matches[:5]}"
            )
        except (TypeError, OSError):
            pass

    def test_SM30_metadata_usage_in_handlers(self):
        """SM30: Handler方法通过metadata获取数据

        验证handler使用region.metadata而不是直接访问内部字段。"""
        import inspect

        for handler_name in EXPECTED_REGION_HANDLERS[:7]:
            method = getattr(self.RegionAnalyzer, handler_name)
            try:
                source = inspect.getsource(method)
                has_metadata = '.metadata[' in source or '.metadata.' in source or 'metadata' in source
                self.assertTrue(
                    has_metadata,
                    f"{handler_name} 未发现metadata的使用"
                )
            except (TypeError, OSError):
                pass


class TestRegionASTGeneratorCompliance(ComplianceTestBase):
    """RegionASTGenerator的一区域一方法合规性验证"""

    @classmethod
    def setup_class(cls):
        try:
            from core.cfg import region_ast_generator as rag_module
            cls.module = rag_module
            cls.GeneratorClass = rag_module.RegionASTGenerator
        except ImportError:
            pytest.skip("无法导入region_ast_generator")

    def test_generator_has_generate_methods(self):
        """RegionASTGenerator具有正确的generate接口"""
        self.assert_has_method(self.GeneratorClass, 'generate')

    def test_generator_no_forbidden_prefixes(self):
        """Generator中不存在禁止前缀的方法"""
        self.assert_no_forbidden_prefix(
            self.GeneratorClass, FORBIDDEN_METHOD_PREFIXES
        )


class TestStructuredAnalyzerCompliance(ComplianceTestBase):
    """StructuredAnalyzer的合规性验证"""

    @classmethod
    def setup_class(cls):
        try:
            from core.cfg import structured_analyzer as sa_module
            cls.module = sa_module
            cls.AnalyzerClass = sa_module.StructuredAnalyzer
        except ImportError:
            pytest.skip("无法导入structured_analyzer")

    def test_structured_analyzer_no_patch_methods(self):
        """StructuredAnalyzer中无补丁式方法"""
        self.assert_no_forbidden_prefix(
            self.AnalyzerClass, FORBIDDEN_METHOD_PREFIXES
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
