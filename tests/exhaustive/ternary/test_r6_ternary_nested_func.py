import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryNestedFunc(ExhaustiveTestCase):
    """Bug R6: ternary 在嵌套函数 return 中 — 字节码不一致。

    原始:
        def outer():
            def inner():
                return a if c else b
    缺陷: 嵌套函数 inner 的 return 是 ternary。期望 inner code object
         内部 ternary 正确归约为 Return(IfExp)；当前疑似嵌套函数的
         code object 边界与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """def outer():
    def inner():
        return a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
