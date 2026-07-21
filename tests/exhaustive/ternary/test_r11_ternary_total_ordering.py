import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTotalOrdering(ExhaustiveTestCase):
    """Bug R11 (new): functools.total_ordering + ternary in __lt__.

    原始:
        from functools import total_ordering
        @total_ordering
        class C:
            def __lt__(self, other):
                return (self.x < other.x if c else False)
            def __eq__(self, other):
                return self.x == other.x
    缺陷: @total_ordering 类装饰器 + ternary return in __lt__。total_ordering
         在类装饰器位置（外层 Call），__build_class__ Call 是内层。__lt__ 内
         return 比较表达式 + ternary。__eq__ return 比较表达式。两个 magic
         method + 装饰器 + ternary merge 块的 RETURN_VALUE 共存。
    """
    SOURCE_CODE = """from functools import total_ordering
@total_ordering
class C:
    def __lt__(self, other):
        return (self.x < other.x if c else False)
    def __eq__(self, other):
        return self.x == other.x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
