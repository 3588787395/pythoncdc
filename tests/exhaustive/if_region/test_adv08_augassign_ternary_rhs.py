import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AugassignTernaryRhs(ExhaustiveTestCase):
    # if 体内 augassign 含三元右值 a += 1 if x else 2
    SOURCE_CODE = """if c:
    a += 1 if x else 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
