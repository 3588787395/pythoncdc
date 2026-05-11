import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedMatchTernary_v1(ExhaustiveTestCase):
    SOURCE_CODE = """match v:
    case _:
        y = x if y else z"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
