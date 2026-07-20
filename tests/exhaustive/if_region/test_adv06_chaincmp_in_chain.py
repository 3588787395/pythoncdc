import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06ChaincmpInChain(ExhaustiveTestCase):
    # if 体内链式 in 比较 (x in y in z) 作赋值右值
    SOURCE_CODE = """if c:
    z = a in b in c"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
