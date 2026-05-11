import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedForMatch_v3(ExhaustiveTestCase):
    SOURCE_CODE = """for k in range(3):
    match u:
        case 1: q = 1
        case _: q = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
