import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInTryExceptFinally(ExhaustiveTestCase):
    """Bug R8: try-except-finally 三分支中 finally 含 ternary — 字节码不一致。

    原始:
        try:
            pass
        except E:
            pass
        finally:
            y = a if c else b
    缺陷: try-except-finally 三分支结构中 finally 含 ternary。
         R7 已测 try-finally + ternary (test_r7_ternary_in_finally) 通过，
         也测过 try-except-finally-finally (test_r7_ternary_in_try_except_finally_finally)。
         R8 测三分支变体确认是否仍稳定，关注 except handler 后 finally
         的 POP_EXCEPT 链与 ternary entry/merge 共享。
    """
    SOURCE_CODE = """try:
    pass
except E:
    pass
finally:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
