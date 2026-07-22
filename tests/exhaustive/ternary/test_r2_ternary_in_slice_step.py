import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInSliceStep(ExhaustiveTestCase):
    """Bug R2-34: ternary 作为 slice 的 step — 字节码不一致。

    原始: x = lst[1:10:a if cond else 1]
    缺陷: ternary 作为 slice step 时，BUILD_SLICE 3 在 merge_block 中消费
         左/右边界（已加载在栈上）和 ternary 结果。反编译器可能丢失
         BUILD_SLICE 3 与外层 BINARY_SUBSCR 结构。
    """
    SOURCE_CODE = """x = lst[1:10:a if cond else 1]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
