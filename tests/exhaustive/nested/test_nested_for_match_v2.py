import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedForMatch_v2(ExhaustiveTestCase):
    SOURCE_CODE = """for j in range(3):
    match w:
        case 1: b = 1
        case _: b = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
