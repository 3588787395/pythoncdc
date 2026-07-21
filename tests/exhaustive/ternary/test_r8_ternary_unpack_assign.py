import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryUnpackAssign(ExhaustiveTestCase):
    """Bug R8: unpacking 赋值 source 是 ternary — 字节码不一致。

    原始:
        *y, = (a if c else b)
    缺陷: unpacking 赋值的源是 ternary。R6 已测过 unpack_assign。
         R8 测 starred target + 单元素 unpack 变体：UNPACK_EX
         在 merge_block 消费 ternary 结果，与 ternary value_target
         推断可能冲突。
    """
    SOURCE_CODE = """*y, = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
