import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedMatchMatch_v2(ExhaustiveTestCase):
    SOURCE_CODE = """match w:
    case _:
        match w:
            case 1: b = 1
            case _: b = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
