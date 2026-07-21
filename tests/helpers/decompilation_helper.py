"""
反编译测试公共辅助模块

提供完备性验证测试矩阵的统一测试基础设施：
- 编译→反编译→验证的完整流程
- 语法正确性检查
- 字节码等价性验证
- AST结构对比

理论依据（编译器测试理论）：
- 回归测试：确保已修复的问题不会重新出现
- 边界值测试：验证极端输入的处理能力
- 组合测试：覆盖控制流结构的所有排列组合
"""

import ast
import dis
import sys
import os
import types
import unittest
from typing import Optional, List, Dict, Any, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.test_functional_verification import (
    DecompilationVerifier,
    VerificationStatus,
    create_test_verifier
)
from tests.control_flow_matrix.base import ControlFlowTestCase


class MatrixTestBase(ControlFlowTestCase):
    """完备性测试矩阵基类

    继承ControlFlowTestCase，增加矩阵测试专用的辅助方法。
    所有矩阵测试用例都应继承此类。

    使用方式：
        class TestBinaryCombination(MatrixTestBase):
            def test_N01_except_while(self):
                source = '''def func(): ...'''
                self.verify_matrix_decompilation(source, 'N01')
    """

    @classmethod
    def setUpClass(cls):
        """初始化验证器（覆盖父类 SOURCE_CODE 强制要求）

        MatrixTestBase 通过 ``verify_matrix_decompilation(source, ...)`` 把源码作为
        参数传入，每个测试方法都有自己的源码，因此不需要类级 ``SOURCE_CODE``
        属性。这里覆盖 ``ControlFlowTestCase.setUpClass``，避免触发其
        ``NotImplementedError("子类必须定义SOURCE_CODE")`` 检查。
        """
        cls.verifier = create_test_verifier()

    setup_class = setUpClass  # pytest nose-style 兼容别名

    def verify_matrix_decompilation(
        self,
        source: str,
        test_id: str = "",
        min_equivalence: float = 0.80,
        timeout: int = 30
    ):
        """
        矩阵测试专用验证流程

        Args:
            source: Python源代码字符串
            test_id: 测试标识符（用于日志）
            min_equivalence: 最小等价率要求
            timeout: 超时时间（秒）

        Returns:
            VerificationReport: 验证报告
        """
        report = self.verifier.verify_decompile(source)

        prefix = f"[{test_id}] " if test_id else ""
        assert report.status in [
            VerificationStatus.PASSED,
            VerificationStatus.WARNING
        ], (
            f"{prefix}反编译验证失败！状态: {report.status.value}\n"
            f"错误: {report.errors}\n"
            f"警告: {report.warnings}\n"
            f"等价率: {report.equivalence_rate:.2%}\n"
            f"反编译结果:\n{report.decompiled_source[:500]}"
        )

        assert report.equivalence_rate >= min_equivalence, (
            f"{prefix}等价率 {report.equivalence_rate:.2%} "
            f"低于阈值 {min_equivalence:.2%}"
        )

        return report

    def verify_syntax_only(self, source: str):
        """仅验证语法正确性（用于已知限制的测试）"""
        code = compile(source.strip(), '<test>', 'exec')
        decompiled = self.decompile_from_code(code)
        tree = ast.parse(decompiled)
        return decompiled

    def decompile_from_code(self, code: types.CodeType) -> str:
        """从code object反编译"""
        from core.cfg import build_cfg
        from core.cfg.region_ast_generator import RegionASTGenerator
        from core.cfg.ast_converter import CFGASTConverter
        from core.cfg.code_generator import CFGCodeGenerator

        cfg = build_cfg(code)
        gen = RegionASTGenerator(cfg, top_level_code=code)
        ast_dict = gen.generate()
        converter = CFGASTConverter()
        py_ast = converter.convert(ast_dict)
        code_gen = CFGCodeGenerator()
        return code_gen.generate(py_ast)

    def count_ast_nodes(self, source: str, node_type: type) -> int:
        """统计源码中指定类型AST节点的数量"""
        tree = ast.parse(source)
        return len([n for n in ast.walk(tree) if isinstance(n, node_type)])

    def get_nesting_depth(self, source: str) -> int:
        """计算源码的最大嵌套深度"""
        tree = ast.parse(source)

        def depth(node, current=0):
            max_d = current
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try,
                                       ast.With, ast.Match, ast.ExceptHandler)):
                    d = depth(child, current + 1)
                    if d > max_d:
                        max_d = d
                else:
                    d = depth(child, current)
                    if d > max_d:
                        max_d = d
            return max_d

        return depth(tree)


class ComplianceTestBase(unittest.TestCase):
    """合规性测试基类

    用于一区域一方法原则、域隔离等架构合规性验证。
    不需要反编译功能，专注于代码结构检查。
    """

    def assert_has_method(self, obj, method_name: str):
        """断言对象具有指定方法"""
        self.assertTrue(
            hasattr(obj, method_name),
            f"缺少必需的方法: {method_name}"
        )
        self.assertTrue(
            callable(getattr(obj, method_name)),
            f"{method_name} 不是可调用对象"
        )

    def assert_no_forbidden_prefix(self, module_class, forbidden_prefixes: Tuple[str, ...]):
        """断言类中不存在禁止前缀的方法"""
        import inspect

        for name, obj in inspect.getmembers(module_class):
            if name.startswith('_') and callable(obj):
                for prefix in forbidden_prefixes:
                    self.assertFalse(
                        name.startswith(prefix),
                        f"发现禁止前缀的方法: {name} (前缀: {prefix})"
                    )

    def get_method_line_count(self, obj, method_name: str) -> int:
        """获取方法的行数"""
        import inspect
        method = getattr(obj, method_name)
        try:
            lines = inspect.getsourcelines(method)
            return len(lines[0])
        except (TypeError, OSError):
            return -1

    def assert_method_length_within(self, obj, method_name: str, max_lines: int):
        """断言方法行数不超过上限"""
        line_count = self.get_method_line_count(obj, method_name)
        if line_count > 0:
            self.assertLessEqual(
                line_count, max_lines,
                f"方法 {method_name} 有 {line_count} 行，超过上限 {max_lines}"
            )


EXPECTED_REGION_HANDLERS = [
    '_handle_sequence_region',
    '_handle_if_then_region',
    '_handle_if_else_region',
    '_handle_if_else_chain_region',
    '_handle_for_loop_region',
    '_handle_while_loop_region',
    '_handle_try_except_region',
    '_handle_try_finally_region',
    '_handle_with_region',
    '_handle_comprehension_region',
    '_handle_function_def_region',
    '_handle_class_def_region',
    '_handle_lambda_region',
    '_handle_ternary_region',
]

FORBIDDEN_METHOD_PREFIXES = (
    '_fix_', '_merge_', '_patch_', '_fallback_',
    '_hack_', '_workaround_', '_temp_',
)
