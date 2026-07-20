import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernarySubscrSubscr(ExhaustiveTestCase):
    # if 条件中三元表达式作下标，且结果继续作下标访问：
    # if d[a if c else b][e] > 0
    # 字节码含两个 BINARY_SUBSCR（第一个 ternary 作下标）。
    SOURCE_CODE = """if d[a if c else b][e] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
