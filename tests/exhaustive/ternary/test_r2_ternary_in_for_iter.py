import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInForIter(ExhaustiveTestCase):
    """Bug R2-22: ternary 作为 for 循环迭代器 — 字节码不一致。

    原始:
        for x in (items if cond else []):
            pass
    缺陷: ternary 作为 for 循环迭代器时，GET_ITER 在 merge_block 中消费
         ternary 结果。反编译器可能丢失 for 循环结构或 ternary 结构。
    """
    SOURCE_CODE = """for x in (items if cond else []):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
