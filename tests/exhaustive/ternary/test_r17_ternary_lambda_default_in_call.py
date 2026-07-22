import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryLambdaDefaultInCall(ExhaustiveTestCase):
    """Bug R17-13: f(g=lambda: a if c else b) — lambda with ternary body as call kwarg。

    原始:
        f(g=lambda: a if c else b)
    缺陷: 函数调用 f 的 keyword 参数 g 的值是 lambda，lambda body 是 ternary。
         lambda 的 code object 内含 ternary region。CALL 指令的 KW_NAMES 与
         MAKE_FUNCTION/KWARGS 协调失败，反编译把 lambda body 退化为
         `lambda *args, **kwargs: None`，丢失 ternary，字节码指令数不匹配 (5 vs 3)。
    """
    SOURCE_CODE = """f(g=lambda: a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
