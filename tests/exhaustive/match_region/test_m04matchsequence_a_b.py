import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM04MatchSequence_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """match [a, b]:
    case [1, 2]:
        pass
    case [3, 4]:
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
