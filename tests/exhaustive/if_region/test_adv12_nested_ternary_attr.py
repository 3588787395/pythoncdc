import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12NestedTernaryAttr(ExhaustiveTestCase):
    # if 条件中嵌套三元表达式作属性访问的 receiver：
    # if (a if c else (b if d else e)).x > 0
    # false 分支本身又是一个三元表达式。
    SOURCE_CODE = """if (a if c else (b if d else e)).x > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
