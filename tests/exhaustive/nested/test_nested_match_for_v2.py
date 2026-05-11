import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedMatchFor_v2(ExhaustiveTestCase):
    SOURCE_CODE = """match w:
    case _:
        for j in r: b += j"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
