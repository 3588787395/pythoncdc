import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInDelAttrSubscript(ExhaustiveTestCase):
    """Bug R7: del 嵌套 attr + subscript ternary — 字节码不一致。

    原始:
        del x.y[a if c else b]
    缺陷: del 的目标是 attr + subscript 组合（x.y[ternary]）。
         R7-04 已测两层 subscript 都是 ternary（完全丢失 del 结构）。
         R7 测 attr + 单 ternary subscript 变体：DELETE_SUBSCR 在
         merge_block 消费 ternary 结果与 x.y 对象，LOAD_ATTR y 与
         ternary entry 块的归属交互可能不同。
    """
    SOURCE_CODE = """del x.y[a if c else b]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
