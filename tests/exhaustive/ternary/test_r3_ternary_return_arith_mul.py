import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryReturnArithMul(ExhaustiveTestCase):
    """Bug R3-06: ternary 在 return + 算术乘 — 字节码不一致。

    原始:
        def f():
            return (a if cond else 1) * 2
    缺陷: ternary 在 return + BINARY_OP 上下文中（乘法），
         merge_context 未识别 return+arith 场景。
    """
    SOURCE_CODE = """def f():
    return (a if cond else 1) * 2
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
