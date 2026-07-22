import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInRaiseNoFrom(ExhaustiveTestCase):
    """Bug R7: raise (ternary) 无 from — 字节码不一致。

    原始:
        raise (a if c else b)
    缺陷: raise 的异常对象是 ternary，无 from 子句。R4 已测 raise from
         (ternary) (test_r4_ternary_in_raise_from)。R3 已测 raise E(ternary)
         (ternary 在 E 调用参数，test_r3_ternary_raise_arg)。R7 测
         raise (ternary) 直接变体：RAISE_VARARGS 1 在 merge_block 消费
         ternary 结果，无 cause 栈值，可能让 ternary value_target 推断
         走不同的分支。
    """
    SOURCE_CODE = """raise (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
