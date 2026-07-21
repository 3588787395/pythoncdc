import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryMagicMethods(ExhaustiveTestCase):
    """Bug R10: magic methods __eq__/__hash__ + ternary — 字节码不一致。

    原始:
        class C:
            def __eq__(self, other):
                return self.x == (other.x if c else 0)
            def __hash__(self):
                return hash(self.x) if c else 0
    缺陷: 两个 magic method 都含 ternary。__eq__ 用作比较，__hash__ 用作
         哈希。两个 ternary 在不同 code object（__eq__ 与 __hash__），
         __hash__ return ternary 是 Return(IfExp)。依「自底向上归约」：
         每个 ternary 在其 code object 内独立归约。R3 已测 return ternary；
         R10 测 magic method 双 ternary 变体，验证不同 magic method 共存时
         ternary 区域归约是否正确。
    """
    SOURCE_CODE = """class C:
    def __eq__(self, other):
        return self.x == (other.x if c else 0)
    def __hash__(self):
        return hash(self.x) if c else 0
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
