import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryForIter(ExhaustiveTestCase):
    """Bug R8: for iter 表达式是 ternary — 字节码不一致。

    原始:
        for x in (a if c else b):
            pass
    缺陷: 同步 for 的 iter 表达式是 ternary。R2 已测过
         ternary_in_for_iter。R8 测变体确认是否仍稳定：ternary merge
         块的 STORE 临时变量作为 GET_ITER 的源，与 for 循环 header
         块的归属可能冲突。
    """
    SOURCE_CODE = """for x in (a if c else b):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
