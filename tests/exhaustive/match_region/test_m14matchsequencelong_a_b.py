import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM14MatchSequenceLong_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """match [a, b, 3]:
    case [1, 2, 3]:
        pass
    case [4, 5, 6]:
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
