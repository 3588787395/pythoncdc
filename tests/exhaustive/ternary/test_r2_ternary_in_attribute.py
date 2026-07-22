import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInAttribute(ExhaustiveTestCase):
    """Bug R2-8: ternary 作为 attribute access 的对象 — 字节码不一致。

    原始: x = (obj if cond else other).attr
    缺陷: ternary 作为 attribute access 的对象时，LOAD_ATTR 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 .attr 与外层赋值。
    """
    SOURCE_CODE = """x = (obj if cond else other).attr"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
