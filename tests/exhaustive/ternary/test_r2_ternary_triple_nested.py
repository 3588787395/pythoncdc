import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryTripleNested(ExhaustiveTestCase):
    """Bug R2-6: 三层嵌套 ternary — 字节码不一致。

    原始: x = a if c1 else b if c2 else c if c3 else d
    缺陷: 三层嵌套 ternary 在 orelse 链中递归。
         反编译器需正确处理嵌套 TernaryRegion 的归约。
    """
    SOURCE_CODE = """x = a if c1 else b if c2 else c if c3 else d"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
