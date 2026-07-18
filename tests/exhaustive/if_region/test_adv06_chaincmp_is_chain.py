import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06ChaincmpIsChain(ExhaustiveTestCase):
    # if 体内链式 is 比较 (x is y is z) 作赋值右值
    SOURCE_CODE = """if c:
    z = a is b is c"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
