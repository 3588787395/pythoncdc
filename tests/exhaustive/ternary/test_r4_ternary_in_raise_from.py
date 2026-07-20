import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInRaiseFrom(ExhaustiveTestCase):
    """Bug R4-19: ternary 在 raise ... from 子句 — 字节码不一致。

    原始: raise E from (a if cond else b)
    缺陷: ternary 在 raise ... from 的 cause 位置时，RAISE_VARARGS 2 在
         merge_block 中消费两个栈值（exception + cause）。R3 已测 raise_arg
         （ternary 在 E(ternary) 调用），R4 测 raise from 子句的不同位置。
         反编译器可能丢失 raise from 结构或 ternary 结构。
    """
    SOURCE_CODE = """raise E from (a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
