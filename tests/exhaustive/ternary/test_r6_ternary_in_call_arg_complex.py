import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryInCallArgComplex(ExhaustiveTestCase):
    """Bug R6: 多个 ternary 在同一调用实参中 — 字节码不一致。

    原始: f(a if c else b, d if e else g, h if i else j)
    缺陷: 同一函数调用含 3 个 ternary 实参。期望 3 个 TernaryRegion 均
         正确归约并被同一 Call 引用；当前疑似多个 TernaryRegion merge
         块共享同一 CALL_FUNCTION 出口导致归属冲突或顺序错乱。
    """
    SOURCE_CODE = """f(a if c else b, d if e else g, h if i else j)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
