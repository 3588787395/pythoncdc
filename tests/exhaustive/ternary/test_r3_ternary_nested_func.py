import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryNestedFunc(ExhaustiveTestCase):
    """Bug R3-13: ternary 在嵌套函数 return 中 — 字节码不一致。

    原始:
        def outer():
            def inner():
                return a if cond else b
            return inner()
    缺陷: 嵌套 code object 内 ternary 重组可能出错。
    """
    SOURCE_CODE = """def outer():
    def inner():
        return a if cond else b
    return inner()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
