import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryListcompCondition(ExhaustiveTestCase):
    """Bug R9: list comprehension 的 condition 是 ternary — 字节码不一致。

    原始:
        x = [i for i in r if (a if c else b)]
    缺陷: list comprehension 的 if 条件是 ternary。listcomp 内部 code
         object 中 ternary merge 块作为 if 条件，与 FOR_ITER + LIST_APPEND
         的栈顺序可能冲突。
    """
    SOURCE_CODE = """x = [i for i in r if (a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
