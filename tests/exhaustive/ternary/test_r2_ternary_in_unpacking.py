import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInUnpacking(ExhaustiveTestCase):
    """Bug R2-24: ternary 在 unpacking 赋值中 — 字节码不一致。

    原始: a, b = (x, y) if cond else (z, w)
    缺陷: ternary 作为 unpacking 赋值的 RHS 时，UNPACK_SEQUENCE 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 unpacking 结构或丢失 a, b 绑定。
    """
    SOURCE_CODE = """a, b = (x, y) if cond else (z, w)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
