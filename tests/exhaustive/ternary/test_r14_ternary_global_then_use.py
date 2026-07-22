import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryGlobalThenUse(ExhaustiveTestCase):
    """Bug R14 (new): global x; x = (a if c else b); y = x — global+ternary+后续使用。

    原始:
        def f():
            global x
            x = (a if c else b)
            y = x
    缺陷: global 声明后 ternary 赋值 x，然后立即用 x 赋值给 y。R7 global_complex 测
         global + ternary。R8 测 global_then_assign。R14 测 global + ternary + 立即
         后续使用 x 的变体：ternary merge 块 STORE_GLOBAL x，然后下一句 LOAD_GLOBAL x
         与 STORE_NAME y 可能与 ternary region 后续块归属冲突。
    """
    SOURCE_CODE = """def f():
    global x
    x = (a if c else b)
    y = x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
