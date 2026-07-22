import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryChainedCall(ExhaustiveTestCase):
    """Bug R13 (new): f(g(h(a if c else b))) — ternary in triple nested call。

    原始:
        f(g(h(a if c else b)))
    缺陷: ternary 在三层嵌套 Call 的最内层。字节码：PUSH_NULL + LOAD f +
         PUSH_NULL + LOAD g + PUSH_NULL + LOAD h + ternary merge + CALL 1
         (h) + CALL 1 (g) + CALL 1 (f)。每个外层 Call 消费内层 Call 的栈顶
         结果。R9 已测 curry_chain 模式（lambda 链），R13 测函数嵌套调用链
         + ternary 在最内层位置。
    """
    SOURCE_CODE = """f(g(h(a if c else b)))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
