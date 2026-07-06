import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM16MatchGuardComplex_n(ExhaustiveTestCase):
    SOURCE_CODE = """match n:
    case int() if n > 0 and n < 100:
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
