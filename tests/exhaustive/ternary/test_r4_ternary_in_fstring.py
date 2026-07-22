import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInFstring(ExhaustiveTestCase):
    """Bug R4-14: ternary 在 f-string 多段插值 — 字节码不一致。

    原始: x = f"{a if cond else b}-{c if d else e}"
    缺陷: 多个 ternary 作为 f-string 的 FormattedValue 时，
         FORMAT_VALUE + BUILD_STRING 在 merge_block 中消费多个 ternary 结果。
         两段插值中间有常量字面量 '-'，BUILD_STRING 3 段需要正确排序。
         反编译器可能丢失 f-string 结构或多 ternary 结构。
    """
    SOURCE_CODE = '''x = f"{a if cond else b}-{c if d else e}"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
