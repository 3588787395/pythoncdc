import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05NestedLambda(ExhaustiveTestCase):
    # if 体内 lambda 嵌套（lambda 内 lambda）
    SOURCE_CODE = """if c:
    f = lambda x: (lambda y: x + y)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
