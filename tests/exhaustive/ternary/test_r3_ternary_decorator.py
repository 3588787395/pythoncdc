import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryDecorator(ExhaustiveTestCase):
    """Bug R3-11: ternary 作为装饰器 — 字节码不一致。

    原始:
        @deco_a if cond else deco_b
        def f():
            pass
    缺陷: ternary 作为装饰器时，MAKE_FUNCTION + CALL 消费 ternary 结果。
         反编译器可能丢失装饰器结构或 ternary 结构。
    """
    SOURCE_CODE = """@(deco_a if cond else deco_b)
def f():
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
