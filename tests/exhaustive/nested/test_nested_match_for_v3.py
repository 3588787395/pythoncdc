import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedMatchFor_v3(ExhaustiveTestCase):
    SOURCE_CODE = """match u:
    case _:
        for k in r: q += k"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
