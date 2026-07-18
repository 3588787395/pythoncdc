import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ForNestedTupleTarget(ExhaustiveTestCase):
    # if 体内 for 循环嵌套元组目标 for (a, b), c in pairs
    SOURCE_CODE = """if c:
    for (a, b), c in pairs:
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
