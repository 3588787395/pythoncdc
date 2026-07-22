import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryTupleSwap(ExhaustiveTestCase):
    """Bug R13 (new): x, y = (a if c else b), (c if d else e) — tuple swap 双 ternary。

    原始:
        x, y = (a if c else b), (c if d else e)
    缺陷: tuple assignment 左右均为双 ternary。右值是 tuple literal
         含两个 ternary 元素。字节码：BUILD_TUPLE 2 在两个 ternary merge
         之后，UNPACK_SEQUENCE 2 + STORE_NAME x + STORE_NAME y。R2 已测
         ternary_in_tuple（单 ternary 元素），R13 测双 ternary 元素 + 多
         目标解包场景。
    """
    SOURCE_CODE = """x, y = (a if c else b), (c if d else e)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
