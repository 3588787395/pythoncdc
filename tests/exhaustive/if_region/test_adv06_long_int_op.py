import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06LongIntOp(ExhaustiveTestCase):
    # if 体内 long int 操作
    SOURCE_CODE = """if c:
    z = 10**100 + x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
