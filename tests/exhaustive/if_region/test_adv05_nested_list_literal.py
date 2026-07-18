import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05NestedListLiteral(ExhaustiveTestCase):
    # if 体内 list 字面量嵌套
    SOURCE_CODE = """if c:
    r = [[a, b], [c, d]]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
