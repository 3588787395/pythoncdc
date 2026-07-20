import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryTryHandler(ExhaustiveTestCase):
    """Bug R3-08: ternary 在 try-except handler 类型中 — 字节码不一致。

    原始:
        try:
            pass
        except (E1 if cond else E2):
            pass
    缺陷: ternary 作为 except handler 的异常类型时，
         DUP_TOP + COMPARE_OP 链消费 ternary 结果。
         反编译器可能丢失 except handler 结构或 ternary 结构。
    """
    SOURCE_CODE = """try:
    pass
except (E1 if cond else E2):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
