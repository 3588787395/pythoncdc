import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryMagicMethods(ExhaustiveTestCase):
    """Bug R10-09 (re-verify in R11): magic methods __eq__/__hash__ + ternary.

    原始:
        class C:
            def __eq__(self, other):
                return self.x == (other.x if c else 0)
            def __hash__(self):
                return (hash(self.x) if c else 0)
    缺陷: 两个 magic method 都含 ternary，在不同 code object 内独立归约。
         __eq__ return 比较表达式，__hash__ return ternary 是 Return(IfExp)。
    """
    SOURCE_CODE = """class C:
    def __eq__(self, other):
        return self.x == (other.x if c else 0)
    def __hash__(self):
        return (hash(self.x) if c else 0)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
