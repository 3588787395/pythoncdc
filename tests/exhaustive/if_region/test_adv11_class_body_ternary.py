import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ClassBodyTernary(ExhaustiveTestCase):
    # if 体内 class body 中赋值右值为三元表达式
    SOURCE_CODE = """if c:
    class C:
        x = a if c2 else b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
