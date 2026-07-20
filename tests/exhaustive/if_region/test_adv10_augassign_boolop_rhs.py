import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10AugassignBoolopRhs(ExhaustiveTestCase):
    # if 体内 augassign 的右值为 boolop x += a and b
    SOURCE_CODE = """if c:
    x += a and b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
