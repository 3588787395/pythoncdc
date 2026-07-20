import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInSet(ExhaustiveTestCase):
    """Bug R2-1: ternary 作为 set 字面量元素 — 字节码不一致。

    原始: s = {a if cond else b}
    缺陷: ternary 在 set 字面量中时，BUILD_SET 消费 ternary 结果。
         反编译器需保留 set 结构。IfExp 在 AST 中存在，
         但字节码指令序列与原始可能不一致。
    """
    SOURCE_CODE = """s = {a if cond else b}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
