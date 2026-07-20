import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05ComplexLiteral(ExhaustiveTestCase):
    # if 体内 complex literal (1+2j)
    SOURCE_CODE = """if c:
    z = 1 + 2j"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
