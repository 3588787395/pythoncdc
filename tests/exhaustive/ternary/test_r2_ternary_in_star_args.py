import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInStarArgs(ExhaustiveTestCase):
    """Bug R2-26: ternary 在 *args 函数调用中 — 字节码不一致。

    原始: print(*(items if cond else []))
    缺陷: ternary 在 *args 中时，BUILD_LIST + LIST_EXTEND 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 * 展开结构。
    """
    SOURCE_CODE = """print(*(items if cond else []))"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
