import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10AugassignCompareRhs(ExhaustiveTestCase):
    # if 体内 augassign 的右值为 compare x += a > b
    SOURCE_CODE = """if c:
    x += a > b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
