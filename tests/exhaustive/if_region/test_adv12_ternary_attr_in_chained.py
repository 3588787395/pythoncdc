import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryAttrInChained(ExhaustiveTestCase):
    # if 条件中三元表达式被属性访问包裹后参与链式比较：
    # if 0 < (a if c else b).x < 10
    # 链式比较的左操作数 0 在 ternary entry 之前加载；中段为 (ternary).x；右操作数 10 在 merge 块加载。
    SOURCE_CODE = """if 0 < (a if c else b).x < 10:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
