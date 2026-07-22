import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInDefaultArg(ExhaustiveTestCase):
    """Bug R2-13: ternary 作为函数默认参数值 — 字节码不一致。

    原始:
        def f(x=a if cond else b):
            return x
    缺陷: ternary 作为函数默认参数值时，BUILD_TUPLE + MAKE_FUNCTION 在 merge_block
         中消费 ternary 结果。反编译器可能丢失默认参数结构。
    """
    SOURCE_CODE = """def f(x=a if cond else b):
    return x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
