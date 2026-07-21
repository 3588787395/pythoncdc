import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryGenexpCondition(ExhaustiveTestCase):
    """Bug R9: generator expression 的 condition 是 ternary — 字节码不一致。

    原始:
        x = sum(i for i in r if (a if c else b))
    缺陷: generator expression 的 if 条件是 ternary。genexp 内部 code
         object 中 ternary merge 块作为 if 条件，与 FOR_ITER + YIELD_VALUE
         的栈顺序、genexp 的 RESUME + GEN_START 协议可能冲突。
    """
    SOURCE_CODE = """x = sum(i for i in r if (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
