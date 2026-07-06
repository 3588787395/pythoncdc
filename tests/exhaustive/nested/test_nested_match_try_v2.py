import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedMatchTry_v2(ExhaustiveTestCase):
    SOURCE_CODE = """match w:
    case _:
        try:
            b = 1
        except:
            b = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
