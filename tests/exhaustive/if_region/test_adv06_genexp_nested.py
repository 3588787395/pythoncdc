import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06GenexpNested(ExhaustiveTestCase):
    # if 体内嵌套生成器表达式 sum(x for x in y)
    SOURCE_CODE = """if c:
    r = sum(x for x in y if x > 0)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
