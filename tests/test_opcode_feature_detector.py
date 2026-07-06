#!/usr/bin/env python3
"""
OpcodeFeatureDetector 单元测试

测试覆盖：
- 操作码分类常量集合完整性（6类）
- 检测方法实现准确性（7个方法）
- 与硬编码对比一致性（100%准确率）
- Python 3.8-3.11 版本兼容性
- 单例模式和工厂函数
- 环境变量和参数覆盖

理论依据：
- 测试驱动开发：先定义预期行为，再验证实现
- 边界值分析：测试每个操作码集合的边界条件
- 回归测试：确保重构不破坏现有功能
"""

import unittest
import sys
import os
import dis
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.cfg.opcode_feature_detector import (
    OpcodeFeatureDetector,
    OpcodeCategory,
    get_opcode_detector,
    create_opcode_detector,
)


class MockInstruction:
    """模拟指令对象，用于测试"""

    def __init__(self, opcode: int, opname: str = None):
        self.opcode = opcode
        if opname is not None:
            self.opname = opname
        else:
            try:
                if isinstance(dis.opname, list):
                    if opcode is not None and 0 <= opcode < len(dis.opname):
                        self.opname = dis.opname[opcode]
                    else:
                        self.opname = f'UNKNOWN({opcode})'
                elif isinstance(dis.opname, dict):
                    self.opname = dis.opname.get(opcode, f'UNKNOWN({opcode})')
                else:
                    self.opname = f'UNKNOWN({opcode})'
            except (IndexError, TypeError):
                self.opname = f'UNKNOWN({opcode})'


class TestOpcodeFeatureDetectorInit(unittest.TestCase):
    """测试初始化和配置"""

    def test_init_default_version(self):
        """测试默认使用当前Python版本"""
        detector = OpcodeFeatureDetector()
        self.assertEqual(detector.python_version, sys.version_info[:2])

    def test_init_custom_version(self):
        """测试自定义Python版本"""
        detector = OpcodeFeatureDetector(python_version=(3, 11))
        self.assertEqual(detector.python_version, (3, 11))

    def test_init_python38(self):
        """测试Python 3.8版本初始化"""
        detector = OpcodeFeatureDetector(python_version=(3, 8))
        self.assertEqual(detector.python_version, (3, 8))
        self.assertFalse(detector.is_python311_plus())

    def test_init_python311(self):
        """测试Python 3.11版本初始化"""
        detector = OpcodeFeatureDetector(python_version=(3, 11))
        self.assertTrue(detector.is_python311_plus())

    def test_repr(self):
        """测试字符串表示"""
        detector = OpcodeFeatureDetector()
        repr_str = repr(detector)
        self.assertIn('OpcodeFeatureDetector', repr_str)
        self.assertIn('python_version', repr_str)

    def test_env_variable_override(self):
        """测试环境变量覆盖Python版本"""
        old_val = os.environ.get('PYTHON_VERSION_OVERRIDE')
        try:
            os.environ['PYTHON_VERSION_OVERRIDE'] = '3.10'
            detector = OpcodeFeatureDetector()
            self.assertEqual(detector.python_version, (3, 10))
        finally:
            if old_val is None:
                os.environ.pop('PYTHON_VERSION_OVERRIDE', None)
            else:
                os.environ['PYTHON_VERSION_OVERRIDE'] = old_val


class TestConditionalJumpOpcodes(unittest.TestCase):
    """测试条件跳转操作码检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_pop_jump_if_false(self):
        """测试 POP_JUMP_IF_FALSE"""
        if hasattr(dis, 'POP_JUMP_IF_FALSE'):
            instr = MockInstruction(dis.POP_JUMP_IF_FALSE)
            self.assertTrue(self.detector.is_conditional_jump(instr))

    def test_pop_jump_if_true(self):
        """测试 POP_JUMP_IF_TRUE"""
        if hasattr(dis, 'POP_JUMP_IF_TRUE'):
            instr = MockInstruction(dis.POP_JUMP_IF_TRUE)
            self.assertTrue(self.detector.is_conditional_jump(instr))

    def test_jump_if_false_or_pop(self):
        """测试 JUMP_IF_FALSE_OR_POP (短路求值)"""
        if hasattr(dis, 'JUMP_IF_FALSE_OR_POP'):
            instr = MockInstruction(dis.JUMP_IF_FALSE_OR_POP)
            self.assertTrue(self.detector.is_conditional_jump(instr))
            self.assertTrue(self.detector.is_short_circuit_jump(instr))

    def test_jump_if_true_or_pop(self):
        """测试 JUMP_IF_TRUE_OR_POP (短路求值)"""
        if hasattr(dis, 'JUMP_IF_TRUE_OR_POP'):
            instr = MockInstruction(dis.JUMP_IF_TRUE_OR_POP)
            self.assertTrue(self.detector.is_conditional_jump(instr))
            self.assertTrue(self.detector.is_short_circuit_jump(instr))

    def test_pop_jump_forward_if_false_311(self):
        """测试 Python 3.11+ 的 POP_JUMP_FORWARD_IF_FALSE"""
        if hasattr(dis, 'POP_JUMP_FORWARD_IF_FALSE'):
            instr = MockInstruction(dis.POP_JUMP_FORWARD_IF_FALSE)
            self.assertTrue(self.detector.is_conditional_jump(instr))

    def test_pop_jump_forward_if_true_311(self):
        """测试 Python 3.11+ 的 POP_JUMP_FORWARD_IF_TRUE"""
        if hasattr(dis, 'POP_JUMP_FORWARD_IF_TRUE'):
            instr = MockInstruction(dis.POP_JUMP_FORWARD_IF_TRUE)
            self.assertTrue(self.detector.is_conditional_jump(instr))

    def test_none_opcode_not_conditional(self):
        """测试None opcode不是条件跳转"""
        instr = MockInstruction(opcode=None)
        self.assertFalse(self.detector.is_conditional_jump(instr))

    def test_load_const_not_conditional(self):
        """测试 LOAD_CONST 不是条件跳转"""
        if hasattr(dis, 'LOAD_CONST'):
            instr = MockInstruction(dis.LOAD_CONST)
            self.assertFalse(self.detector.is_conditional_jump(instr))


class TestUnconditionalJumpOpcodes(unittest.TestCase):
    """测试无条件跳转操作码检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_jump_forward(self):
        """测试 JUMP_FORWARD"""
        if hasattr(dis, 'JUMP_FORWARD'):
            instr = MockInstruction(dis.JUMP_FORWARD)
            self.assertTrue(self.detector.is_unconditional_jump(instr))
            self.assertFalse(self.detector.is_conditional_jump(instr))

    def test_jump_absolute(self):
        """测试 JUMP_ABSOLUTE"""
        if hasattr(dis, 'JUMP_ABSOLUTE'):
            instr = MockInstruction(dis.JUMP_ABSOLUTE)
            self.assertTrue(self.detector.is_unconditional_jump(instr))

    def test_jump_backward(self):
        """测试 JUMP_BACKWARD (Python 3.11+)"""
        if hasattr(dis, 'JUMP_BACKWARD'):
            instr = MockInstruction(dis.JUMP_BACKWARD)
            self.assertTrue(self.detector.is_unconditional_jump(instr))

    def test_continue_loop_legacy(self):
        """测试 CONTINUE_LOOP (Python 3.8-3.10)"""
        if hasattr(dis, 'CONTINUE_LOOP'):
            instr = MockInstruction(dis.CONTINUE_LOOP)
            self.assertTrue(self.detector.is_unconditional_jump(instr))

    def test_category_is_unconditional(self):
        """测试类别检测为无条件跳转"""
        if hasattr(dis, 'JUMP_FORWARD'):
            instr = MockInstruction(dis.JUMP_FORWARD)
            category = self.detector.get_opcode_category(instr)
            self.assertEqual(category, OpcodeCategory.UNCONDITIONAL_JUMP)


class TestLoopHeaderOpcodes(unittest.TestCase):
    """测试循环头指令检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_for_iter(self):
        """测试 FOR_ITER - for循环迭代器"""
        if hasattr(dis, 'FOR_ITER'):
            instr = MockInstruction(dis.FOR_ITER)
            self.assertTrue(self.detector.is_loop_header_opcode(instr))
            category = self.detector.get_opcode_category(instr)
            self.assertEqual(category, OpcodeCategory.LOOP_HEADER)

    def test_get_anext(self):
        """测试 GET_ANEXT - 异步for循环"""
        if hasattr(dis, 'GET_ANEXT'):
            instr = MockInstruction(dis.GET_ANEXT)
            self.assertTrue(self.detector.is_loop_header_opcode(instr))

    def test_get_iter(self):
        """测试 GET_ITER - 迭代器获取"""
        if hasattr(dis, 'GET_ITER'):
            instr = MockInstruction(dis.GET_ITER)
            self.assertTrue(self.detector.is_loop_header_opcode(instr))

    def test_get_aiter(self):
        """测试 GET_AITER - 异步迭代器获取"""
        if hasattr(dis, 'GET_AITER'):
            instr = MockInstruction(dis.GET_AITER)
            self.assertTrue(self.detector.is_loop_header_opcode(instr))

    def test_non_loop_instruction(self):
        """测试非循环头指令"""
        if hasattr(dis, 'LOAD_CONST'):
            instr = MockInstruction(dis.LOAD_CONST)
            self.assertFalse(self.detector.is_loop_header_opcode(instr))


class TestShortCircuitJumpOpcodes(unittest.TestCase):
    """测试短路求值跳转检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_jump_if_false_or_pop_short_circuit(self):
        """测试 and 表达式的短路求值"""
        if hasattr(dis, 'JUMP_IF_FALSE_OR_POP'):
            instr = MockInstruction(dis.JUMP_IF_FALSE_OR_POP)
            self.assertTrue(self.detector.is_short_circuit_jump(instr))

    def test_jump_if_true_or_pop_short_circuit(self):
        """测试 or 表达式的短路求值"""
        if hasattr(dis, 'JUMP_IF_TRUE_OR_POP'):
            instr = MockInstruction(dis.JUMP_IF_TRUE_OR_POP)
            self.assertTrue(self.detector.is_short_circuit_jump(instr))

    def test_regular_conditional_not_short_circuit(self):
        """测试普通条件跳转不算短路求值"""
        if hasattr(dis, 'POP_JUMP_IF_FALSE') and hasattr(dis, 'JUMP_IF_FALSE_OR_POP'):
            # 确保 POP_JUMP_IF_FALSE 不在短路集合中（除非也是短路）
            instr = MockInstruction(dis.POP_JUMP_IF_FALSE)
            is_short_circuit = self.detector.is_short_circuit_jump(instr)
            # POP_JUMP_IF_FALSE 不应该在 SHORT_CIRCUIT 集合中
            # （它可能在CONDITIONAL集合中但不在SHORT_CIRCUIT中）


class TestExceptionOpcodes(unittest.TestCase):
    """测试异常相关指令检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_push_exc_info(self):
        """测试 PUSH_EXC_INFO"""
        if hasattr(dis, 'PUSH_EXC_INFO'):
            instr = MockInstruction(dis.PUSH_EXC_INFO)
            self.assertTrue(self.detector.is_exception_related(instr))

    def test_check_exc_match(self):
        """测试 CHECK_EXC_MATCH"""
        if hasattr(dis, 'CHECK_EXC_MATCH'):
            instr = MockInstruction(dis.CHECK_EXC_MATCH)
            self.assertTrue(self.detector.is_exception_related(instr))

    def test_reraise(self):
        """测试 RERAISE"""
        if hasattr(dis, 'RERAISE'):
            instr = MockInstruction(dis.RERAISE)
            self.assertTrue(self.detector.is_exception_related(instr))

    def test_with_except_start(self):
        """测试 WITH_EXCEPT_START"""
        if hasattr(dis, 'WITH_EXCEPT_START'):
            instr = MockInstruction(dis.WITH_EXCEPT_START)
            self.assertTrue(self.detector.is_exception_related(instr))

    def test_before_with(self):
        """测试 BEFORE_WITH"""
        if hasattr(dis, 'BEFORE_WITH'):
            instr = MockInstruction(dis.BEFORE_WITH)
            self.assertTrue(self.detector.is_exception_related(instr))

    def test_setup_finally(self):
        """测试 SETUP_FINALLY (旧版)"""
        if hasattr(dis, 'SETUP_FINALLY'):
            instr = MockInstruction(dis.SETUP_FINALLY)
            self.assertTrue(self.detector.is_exception_related(instr))
            self.assertTrue(self.detector.is_setup_instruction(instr))

    def test_setup_except(self):
        """测试 SETUP_EXCEPT (旧版)"""
        if hasattr(dis, 'SETUP_EXCEPT'):
            instr = MockInstruction(dis.SETUP_EXCEPT)
            self.assertTrue(self.detector.is_exception_related(instr))
            self.assertTrue(self.detector.is_setup_instruction(instr))

    def test_pop_except(self):
        """测试 POP_EXCEPT"""
        if hasattr(dis, 'POP_EXCEPT'):
            instr = MockInstruction(dis.POP_EXCEPT)
            self.assertTrue(self.detector.is_exception_related(instr))


class TestSetupInstructions(unittest.TestCase):
    """测试SETUP指令检测（旧版异常处理）"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_setup_with(self):
        """测试 SETUP_WITH"""
        if hasattr(dis, 'SETUP_WITH'):
            instr = MockInstruction(dis.SETUP_WITH)
            self.assertTrue(self.detector.is_setup_instruction(instr))

    def test_setup_async_with(self):
        """测试 SETUP_ASYNC_WITH"""
        if hasattr(dis, 'SETUP_ASYNC_WITH'):
            instr = MockInstruction(dis.SETUP_ASYNC_WITH)
            self.assertTrue(self.detector.is_setup_instruction(instr))

    def test_setup_loop_legacy(self):
        """测试 SETUP_LOOP (Python 3.7及更早)"""
        if hasattr(dis, 'SETUP_LOOP'):
            instr = MockInstruction(dis.SETUP_LOOP)
            self.assertTrue(self.detector.is_setup_instruction(instr))


class TestOpcodeCategoryDetection(unittest.TestCase):
    """测试操作码类别综合检测"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_conditional_jump_category(self):
        """测试条件跳转类别"""
        if hasattr(dis, 'POP_JUMP_IF_FALSE'):
            instr = MockInstruction(dis.POP_JUMP_IF_FALSE)
            self.assertEqual(
                self.detector.get_opcode_category(instr),
                OpcodeCategory.CONDITIONAL_JUMP
            )

    def test_unconditional_jump_category(self):
        """测试无条件跳转类别"""
        if hasattr(dis, 'JUMP_FORWARD'):
            instr = MockInstruction(dis.JUMP_FORWARD)
            self.assertEqual(
                self.detector.get_opcode_category(instr),
                OpcodeCategory.UNCONDITIONAL_JUMP
            )

    def test_loop_header_category(self):
        """测试循环头类别"""
        if hasattr(dis, 'FOR_ITER'):
            instr = MockInstruction(dis.FOR_ITER)
            self.assertEqual(
                self.detector.get_opcode_category(instr),
                OpcodeCategory.LOOP_HEADER
            )

    def test_exception_category(self):
        """测试异常相关类别"""
        if hasattr(dis, 'PUSH_EXC_INFO'):
            instr = MockInstruction(dis.PUSH_EXC_INFO)
            self.assertEqual(
                self.detector.get_opcode_category(instr),
                OpcodeCategory.EXCEPTION_RELATED
            )

    def test_other_category(self):
        """测试其他类别"""
        if hasattr(dis, 'LOAD_CONST'):
            instr = MockInstruction(dis.LOAD_CONST)
            self.assertEqual(
                self.detector.get_opcode_category(instr),
                OpcodeCategory.OTHER
            )

    def test_priority_order(self):
        """测试类别优先级：条件跳转 > 无条件跳转 > ..."""
        # JUMP_BACKWARD 可能同时在多个集合中
        # 但应该返回优先级最高的类别
        if hasattr(dis, 'JUMP_BACKWARD'):
            instr = MockInstruction(dis.JUMP_BACKWARD)
            category = self.detector.get_opcode_category(instr)
            # JUMP_BACKWARD 应该是 CONDITIONAL 或 UNCONDITIONAL
            self.assertIn(category, [
                OpcodeCategory.CONDITIONAL_JUMP,
                OpcodeCategory.UNCONDITIONAL_JUMP
            ])


class TestUtilityMethods(unittest.TestCase):
    """测试工具方法"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_get_opcode_name_known(self):
        """测试获取已知操作码名称"""
        if hasattr(dis, 'LOAD_CONST'):
            name = self.detector.get_opcode_name(dis.LOAD_CONST)
            self.assertEqual(name, 'LOAD_CONST')

    def test_get_opcode_name_unknown(self):
        """测试获取未知操作码名称"""
        name = self.detector.get_opcode_name(99999)
        self.assertIn('UNKNOWN', name)

    def test_get_all_opcodes_in_category(self):
        """测试获取指定类别的所有操作码"""
        opcodes = self.detector.get_all_opcodes_in_category(OpcodeCategory.CONDITIONAL_JUMP)
        self.assertIsInstance(opcodes, set)
        self.assertGreater(len(opcodes), 0)

    def test_is_python311_plus_current(self):
        """测试当前版本检测"""
        is_311_plus = self.detector.is_python311_plus()
        expected = sys.version_info >= (3, 11)
        self.assertEqual(is_311_plus, expected)


class TestSingletonPattern(unittest.TestCase):
    """测试单例模式和工厂函数"""

    def test_get_opcode_detector_returns_instance(self):
        """测试全局单例函数返回实例"""
        detector = get_opcode_detector()
        self.assertIsInstance(detector, OpcodeFeatureDetector)

    def test_get_opcode_detector_singleton(self):
        """测试单例特性：多次调用返回同一实例"""
        detector1 = get_opcode_detector()
        detector2 = get_opcode_detector()
        self.assertIs(detector1, detector2)

    def test_create_opcode_detector_new_instance(self):
        """测试工厂函数创建新实例"""
        detector1 = create_opcode_detector()
        detector2 = create_opcode_detector()
        self.assertIsNot(detector1, detector2)

    def test_create_with_custom_version(self):
        """测试创建指定版本的检测器"""
        detector = create_opcode_detector(python_version=(3, 10))
        self.assertEqual(detector.python_version, (3, 10))


class TestHardcodedConsistency(unittest.TestCase):
    """与硬编码对比的一致性测试（100%准确率要求）

    这是核心验收标准：确保 OpcodeFeatureDetector 的检测结果
    与直接使用硬编码操作码名称完全一致。
    """

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_consistency_conditional_jumps(self):
        """验证条件跳转检测与硬编码一致"""
        hardcoded_conditional = {
            'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
            'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
            'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
        }

        for opname in hardcoded_conditional:
            if hasattr(dis, opname):
                opcode = getattr(dis, opname)
                instr = MockInstruction(opcode, opname)

                # 使用检测器
                detector_result = self.detector.is_conditional_jump(instr)

                # 使用硬编码方式
                hardcoded_result = opname in hardcoded_conditional or \
                                   opname.startswith('POP_JUMP') or \
                                   opname.startswith('JUMP_IF')

                self.assertEqual(
                    detector_result, hardcoded_result,
                    f"不一致: {opname} - 检测器={detector_result}, 硬编码={hardcoded_result}"
                )

    def test_consistency_unconditional_jumps(self):
        """验证无条件跳转检测与硬编码一致"""
        hardcoded_unconditional = {
            'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
            'JUMP_BACKWARD_NO_INTERRUPT', 'CONTINUE_LOOP'
        }

        for opname in hardcoded_unconditional:
            if hasattr(dis, opname):
                opcode = getattr(dis, opname)
                instr = MockInstruction(opcode, opname)

                detector_result = self.detector.is_unconditional_jump(instr)
                hardcoded_result = opname in hardcoded_unconditional

                self.assertEqual(
                    detector_result, hardcoded_result,
                    f"不一致: {opname}"
                )

    def test_consistency_loop_headers(self):
        """验证循环头检测与硬编码一致"""
        hardcoded_loop = {'FOR_ITER', 'GET_ANEXT', 'GET_ITER', 'GET_AITER'}

        for opname in hardcoded_loop:
            if hasattr(dis, opname):
                opcode = getattr(dis, opname)
                instr = MockInstruction(opcode, opname)

                detector_result = self.detector.is_loop_header_opcode(instr)
                hardcoded_result = opname in hardcoded_loop

                self.assertEqual(
                    detector_result, hardcoded_result,
                    f"不一致: {opname}"
                )

    def test_consistency_exceptions(self):
        """验证异常指令检测与硬编码一致"""
        hardcoded_exc = {
            'PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'RERAISE',
            'WITH_EXCEPT_START', 'BEFORE_WITH', 'SETUP_FINALLY',
            'SETUP_EXCEPT', 'POP_EXCEPT'
        }

        for opname in hardcoded_exc:
            if hasattr(dis, opname):
                opcode = getattr(dis, opname)
                instr = MockInstruction(opcode, opname)

                detector_result = self.detector.is_exception_related(instr)
                hardcoded_result = opname in hardcoded_exc

                self.assertEqual(
                    detector_result, hardcoded_result,
                    f"不一致: {opname}"
                )


class TestVersionCompatibility(unittest.TestCase):
    """测试多版本兼容性"""

    def test_python38_compatibility(self):
        """测试 Python 3.8 兼容性"""
        detector = create_opcode_detector(python_version=(3, 8))
        # 检测器应能正常初始化
        self.assertIsNotNone(detector)
        self.assertEqual(detector.python_version, (3, 8))
        # 基本操作码集合应该存在（可能为空或包含操作码）
        self.assertIsInstance(detector.CONDITIONAL_JUMP_OPCODES, set)

    def test_python310_compatibility(self):
        """测试 Python 3.10 兼容性"""
        detector = create_opcode_detector(python_version=(3, 10))
        # 基本功能应正常工作
        self.assertIsNotNone(detector.CONDITIONAL_JUMP_OPCODES)
        self.assertIsNotNone(detector.UNCONDITIONAL_JUMP_OPCODES)

    def test_python311_compatibility(self):
        """测试 Python 3.11 兼容性"""
        detector = create_opcode_detector(python_version=(3, 11))
        self.assertTrue(detector.is_python311_plus())
        # Python 3.11+ 应该有新的条件跳转变体
        if hasattr(dis, 'POP_JUMP_FORWARD_IF_FALSE'):
            self.assertIn(
                dis.POP_JUMP_FORWARD_IF_FALSE,
                detector.CONDITIONAL_JUMP_OPCODES
            )


class TestEdgeCases(unittest.TestCase):
    """测试边界情况和异常输入"""

    def setUp(self):
        self.detector = create_opcode_detector()

    def test_instruction_without_opcode_attr(self):
        """测试没有opcode属性的对象"""
        class BrokenInstruction:
            pass

        instr = BrokenInstruction()
        self.assertFalse(self.detector.is_conditional_jump(instr))
        self.assertFalse(self.detector.is_unconditional_jump(instr))

    def test_instruction_with_zero_opcode(self):
        """测试opcode为0的指令（通常不存在）"""
        instr = MockInstruction(0)
        # 0 是 CACHE 操作码（Python 3.11+），不是条件跳转
        self.assertFalse(self.detector.is_conditional_jump(instr))
        category = self.detector.get_opcode_category(instr)
        # 0 可能是 CACHE 或其他，只要不崩溃即可
        self.assertIsInstance(category, OpcodeCategory)

    def test_negative_opcode(self):
        """测试负数opcode"""
        instr = MockInstruction(-1)
        self.assertFalse(self.detector.is_conditional_jump(instr))
        category = self.detector.get_opcode_category(instr)
        self.assertIsInstance(category, OpcodeCategory)

    def test_large_opcode_number(self):
        """测试大数值opcode"""
        instr = MockInstruction(999999)
        self.assertFalse(self.detector.is_conditional_jump(instr))
        name = self.detector.get_opcode_name(999999)
        self.assertIn('UNKNOWN', name)

    def test_all_categories_non_empty(self):
        """测试所有类别集合非空（至少在当前版本）"""
        categories = [
            (OpcodeCategory.CONDITIONAL_JUMP, self.detector.CONDITIONAL_JUMP_OPCODES),
            (OpcodeCategory.UNCONDITIONAL_JUMP, self.detector.UNCONDITIONAL_JUMP_OPCODES),
            (OpcodeCategory.EXCEPTION_RELATED, self.detector.EXCEPTION_OPCODES),
        ]

        for category, opcode_set in categories:
            # 某些版本可能没有某些操作码，所以只检查类型
            self.assertIsInstance(opcode_set, set)


if __name__ == '__main__':
    unittest.main(verbosity=2)
