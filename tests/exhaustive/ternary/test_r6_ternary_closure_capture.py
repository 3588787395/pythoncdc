import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryClosureCapture(ExhaustiveTestCase):
    """Bug R6: ternary 在闭包中捕获外层变量 — 字节码不一致。

    原始:
        def f():
            x = 1
            def g():
                return x if c else 0
            return g
    缺陷: 闭包 g 捕获外层 x，且 g 的 return 是 ternary。期望 g code
         object 内部 ternary 正确归约并捕获 x (LOAD_DEREF)；当前疑似
         闭包的 LOAD_DEREF 与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """def f():
    x = 1
    def g():
        return x if c else 0
    return g
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
