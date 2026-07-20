import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInDelTargetComplex(ExhaustiveTestCase):
    """Bug R7: del 嵌套 subscript 两层都是 ternary — 字节码不一致。

    原始:
        del x[a if c else b][c if d else e]
    缺陷: del 的 subscript 目标使用嵌套 ternary（两层 subscript 索引
         都是 ternary）。R4 已测单层 del subscript ternary
         (test_r4_ternary_in_del_target)，R7 测两层嵌套 subscript
         变体：DELETE_SUBSCR 在最外层 merge_block 消费栈值，而两个
         ternary 的 merge 块各自产生索引值，两个 ternary 的归约顺序
         与栈消费顺序可能冲突。
    """
    SOURCE_CODE = """del x[a if c else b][c if d else e]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
