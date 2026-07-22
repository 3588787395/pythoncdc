import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryReceiverMethodCall(ExhaustiveTestCase):
    """Bug R13 (new): (a if c else b).method() — ternary as method call receiver。

    原始:
        (a if c else b).method()
    缺陷: ternary 作为 method call 的 receiver。LOAD_METHOD 之前需要先求值
         ternary（receiver），然后 LOAD_METHOD method 消费 receiver 栈顶。
         ternary merge 块栈输出作为 LOAD_METHOD 的 receiver。R2 已测 ternary
         _method_chain (ternary 在 method chain 中间)，R13 测 ternary 作为
         单一 receiver 的最简单场景。
    """
    SOURCE_CODE = """(a if c else b).method()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
