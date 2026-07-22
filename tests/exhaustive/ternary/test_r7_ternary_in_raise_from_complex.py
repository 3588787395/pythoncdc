import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInRaiseFromComplex(ExhaustiveTestCase):
    """Bug R7: raise from 子句 cause 是嵌套 ternary — 字节码不一致。

    原始:
        raise E from (a if c else (b if d else e))
    缺陷: raise from 的 cause 位置使用嵌套 ternary。R4 已测单层
         raise from ternary (test_r4_ternary_in_raise_from)，R7 测
         嵌套 ternary 变体：RAISE_VARARGS 2 在最外层 merge_block
         消费两个栈值（exception + cause），而 cause 由嵌套 ternary
         产生，嵌套 ternary 的内部归约可能与外层 merge 的栈消费
         冲突。
    """
    SOURCE_CODE = """raise E from (a if c else (b if d else e))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
