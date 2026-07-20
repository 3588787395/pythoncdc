import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05ParenTupleAssign(ExhaustiveTestCase):
    # if 体内元组字面量作赋值目标 (a, b) = (1, 2)
    SOURCE_CODE = """if c:
    (a, b) = (1, 2)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
