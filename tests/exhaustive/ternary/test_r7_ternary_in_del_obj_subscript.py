import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInDelObjSubscript(ExhaustiveTestCase):
    """Bug R7: del (ternary)[idx] — ternary 作为 del 的 base 对象 — 字节码不一致。

    原始:
        del (a if c else b)[idx]
    缺陷: del 的 subscript 目标的 base 对象是 ternary。R7-04 已测
         两层 subscript 索引都是 ternary（完全丢失 del 结构）。
         R7 测 base 是 ternary 变体：DELETE_SUBSCR 在 merge_block
         消费 ternary 结果与 idx，ternary entry 在 LOAD x 之前，
         可能与 R7-04 的栈消费顺序不同，暴露不同的退化模式。
    """
    SOURCE_CODE = """del (a if c else b)[idx]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
