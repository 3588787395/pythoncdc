import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryMultiSameConsumer(ExhaustiveTestCase):
    """Bug R8: 多 ternary 共享同一 call consumer — 字节码不一致。

    原始:
        f(a if c1 else b, d if c2 else e)
    缺陷: 函数调用有两个 ternary 参数。R5 已测 ternary_in_call_arg_complex。
         R8 测两个独立 ternary 共享同一 call consumer 变体：两个 ternary
         的 merge 块都进入同一 PRECALL+CALL，栈顺序与 ternary chain
         检测可能冲突。
    """
    SOURCE_CODE = """f(a if c1 else b, d if c2 else e)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
