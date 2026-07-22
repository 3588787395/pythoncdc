import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryYieldComplex(ExhaustiveTestCase):
    """Bug R6: yield + 嵌套 ternary — 字节码不一致。

    原始:
        def g():
            yield (a if c else b) if d else (e if f else h)
    缺陷: generator 函数中 yield 的是嵌套 ternary (顶层 ternary 的两个
         分支都是 ternary)。期望嵌套 TernaryRegion 均正确归约并嵌套为
         Yield(IfExp(IfExp, IfExp))；当前疑似嵌套 ternary merge 块与
         YIELD_VALUE 出口交互产生归属冲突。
    """
    SOURCE_CODE = """def g():
    yield (a if c else b) if d else (e if f else h)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
