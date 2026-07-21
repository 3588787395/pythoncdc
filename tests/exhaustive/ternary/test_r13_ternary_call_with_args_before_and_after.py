import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryCallWithArgsBeforeAndAfter(ExhaustiveTestCase):
    """Bug R13 (new): f(g(0), (a if c else b), h(1)) — ternary sandwiched by calls。

    原始:
        f(g(0), (a if c else b), h(1))
    缺陷: ternary 作为多参数 Call 的中间位置参数，前后参数都是嵌套 Call。
         字节码复杂：PUSH_NULL + LOAD f + PUSH_NULL + LOAD g + LOAD_CONST 0 +
         PRECALL + CALL 1 + ternary merge + PUSH_NULL + LOAD h + LOAD_CONST 1 +
         PRECALL + CALL 1 + PRECALL + CALL 3 (f)。验证 ternary 在嵌套 Call 链
         中作为位置参数 + 兄弟参数也是 Call 的归约。
    """
    SOURCE_CODE = """f(g(0), (a if c else b), h(1))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
