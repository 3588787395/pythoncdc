import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryInLambdaBodyComplex(ExhaustiveTestCase):
    """Bug R6: 多个 ternary 在 lambda body 中 — 字节码不一致。

    原始: f = lambda: (a if c else b) + (d if e else g)
    缺陷: lambda body 是两个 ternary 的算术组合。期望 lambda code
         object 内部两个 TernaryRegion 均正确归约并被 BinOp 引用；
         当前疑似两个 TernaryRegion merge 块共享同一 BINARY_OP 出口
         导致归属冲突。
    """
    SOURCE_CODE = """f = lambda: (a if c else b) + (d if e else g)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
