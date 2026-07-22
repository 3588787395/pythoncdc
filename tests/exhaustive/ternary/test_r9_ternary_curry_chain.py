import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryCurryChain(ExhaustiveTestCase):
    """Bug R9: curry chain + ternary — 字节码不一致。

    原始:
        f = lambda x: lambda y: lambda z: (x if c else y) + z
    缺陷: 三层 lambda 嵌套（curry chain），最内层 lambda body 含 ternary
         + binop。ternary merge 块作为 BINARY_OP 的左操作数，与三层
         lambda 的 LOAD_DEREF 闭包变量捕获可能冲突。
    """
    SOURCE_CODE = """f = lambda x: lambda y: lambda z: (x if c else y) + z
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
