"""
控制流完备性测试矩阵

提供100+个测试用例，覆盖Python控制流语法的所有主要模式：
- L1: 基本结构（52项）
- L1_EXP: 表达式级（12项）
- L1_CF: 函数/类定义（12项）
- L2: 两层嵌套（30项）
- L2_EX: 两层穷举组合（48项）
- L3: 三层嵌套（18项）
- L3_CO: 三层组合（16项）

使用方法：
    python -m pytest tests/control_flow_matrix/ -v
    或
    python tests/control_flow_matrix/run_tests.py
"""

from .base import ControlFlowTestCase

__all__ = ['ControlFlowTestCase']
__version__ = '1.1.0'
