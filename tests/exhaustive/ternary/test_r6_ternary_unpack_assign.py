import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryUnpackAssign(ExhaustiveTestCase):
    """Bug R6: 多个 ternary 在 tuple unpack 赋值中 — 字节码不一致。

    原始: x, y = (a if c else b), (d if e else f)
    缺陷: tuple unpack 赋值中 RHS 含两个独立 ternary，期望两个 TernaryRegion
         均正确归约并被 tuple + unpack 引用；当前疑似多个 TernaryRegion
         共享同一 unpack 序列导致归属冲突。
    """
    SOURCE_CODE = """x, y = (a if c else b), (d if e else f)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
