import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07BoolShortCircuitRhs(ExhaustiveTestCase):
    # if 体内 boolean 短路作赋值右值: x = a and b or c
    SOURCE_CODE = """if c:
    r = a and b or cc"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
