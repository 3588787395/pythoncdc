import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernarySubscrAttr(ExhaustiveTestCase):
    # if 条件中三元表达式作下标，且结果继续作属性访问：
    # if d[a if c else b].x > 0
    # 字节码含 BINARY_SUBSCR（ternary 作下标）+ LOAD_ATTR。
    SOURCE_CODE = """if d[a if c else b].x > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
