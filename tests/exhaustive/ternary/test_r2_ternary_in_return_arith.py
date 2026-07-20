import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInReturnArith(ExhaustiveTestCase):
    """Bug R2-10: ternary 在 return 语句的算术表达式中 — 字节码不一致。

    原始:
        def f():
            return (a if cond else 0) + 1
    缺陷: 嵌套 code object 中，ternary 在 return 语句的算术表达式里，
         反编译器可能丢失 + 1 与 return 结构。
    """
    SOURCE_CODE = """def f():
    return (a if cond else 0) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
