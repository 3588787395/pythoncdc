import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryAttrAssign(ExhaustiveTestCase):
    # if 体内三元作属性赋值右值 a.b = c if cond else d
    SOURCE_CODE = """if c:
    a.b = c if cond else d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
