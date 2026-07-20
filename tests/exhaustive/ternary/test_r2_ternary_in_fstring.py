import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInFstring(ExhaustiveTestCase):
    """Bug R2-14: ternary 在 f-string 表达式中 — 字节码不一致。

    原始: x = f"{a if cond else b}"
    缺陷: ternary 在 f-string 中作为 FormattedValue 时，FORMAT_VALUE 和
         BUILD_STRING 在 merge_block 中消费 ternary 结果。
         反编译器可能丢失 f-string 结构。
    """
    SOURCE_CODE = '''x = f"{a if cond else b}"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
