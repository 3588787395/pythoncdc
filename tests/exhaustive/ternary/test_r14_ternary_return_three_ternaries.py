import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryReturnThreeTernaries(ExhaustiveTestCase):
    """Bug R14 (new): return (t1), (t2), (t3) — return 三元组三个 ternary。

    原始:
        def f():
            return (a if c else b), (d if e else f), (g if h else i)
    缺陷: return 多元组，每个元素都是 ternary。R3 return_tuple 已测 return
         单 ternary 元组。R1 return_tuple_with_ternary 测过类似。R14 测三个
         ternary 共存变体：三个 ternary region 同时归约，每个 merge 块栈顶
         与 BUILD_TUPLE 3 一起合成 Tuple。可能引发 chained ternary 识别冲突
         或 region 边界归属冲突。
    """
    SOURCE_CODE = """def f():
    return (a if c else b), (d if e else f), (g if h else i)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
