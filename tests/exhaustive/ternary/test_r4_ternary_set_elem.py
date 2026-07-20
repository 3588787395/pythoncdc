import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernarySetElem(ExhaustiveTestCase):
    """Bug R4-09: ternary 作为 set 多元素（3 元素场景）— 字节码不一致。

    原始: s = {a if cond else b, c if d else e, f if g else h}
    缺陷: 多个 ternary 作为 set 元素时，BUILD_SET 在 merge_block 中消费
         多个 ternary 结果。三个 ternary 的 merge_block 链式合并复杂，
         反编译器可能丢失 set 结构或多 ternary 结构。
    """
    SOURCE_CODE = """s = {a if cond else b, c if d else e, f if g else h}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
