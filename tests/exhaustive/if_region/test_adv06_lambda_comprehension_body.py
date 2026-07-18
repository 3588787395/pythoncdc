import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06LambdaComprehensionBody(ExhaustiveTestCase):
    # if 体内 lambda 嵌套推导式作为函数体
    SOURCE_CODE = """if c:
    f = lambda x: [y for y in x if y > 0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
