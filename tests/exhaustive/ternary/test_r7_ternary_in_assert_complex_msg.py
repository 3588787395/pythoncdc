import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAssertComplexMsg(ExhaustiveTestCase):
    """Bug R7: assert 的 message 是 ternary 调用 — 字节码不一致。

    原始:
        assert x, f(a if c else b)
    缺陷: assert 的 message 位置是 f(ternary) 调用。R7-01 已测简单
         assert x, (ternary) 变体（反编译为 assert x + raise (ternary)()，
         ternary 错误添加 () 调用）。R7 测 f(ternary) 变体：原本就是
         调用，反编译器的 () 添加 bug 可能让调用嵌套层级错乱。
    """
    SOURCE_CODE = """assert x, f(a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
