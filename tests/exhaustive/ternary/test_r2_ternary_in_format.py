import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInFormat(ExhaustiveTestCase):
    """Bug R2-21: ternary 在字符串 % 格式化中 — 字节码不一致。

    原始: x = "%s" % (a if cond else b)
    缺陷: ternary 作为字符串格式化参数时，BINARY_OP(%) 在 merge_block 中
         消费 format 字符串和 ternary 结果。反编译器可能丢失 % 操作。
    """
    SOURCE_CODE = '''x = "%s" % (a if cond else b)'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
