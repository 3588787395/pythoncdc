import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AugassignBinopRhs(ExhaustiveTestCase):
    # if 体内 augassign 复杂右值 a += b * c + d
    SOURCE_CODE = """if c:
    a += b * c + d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
