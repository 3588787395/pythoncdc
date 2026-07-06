import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM19MatchStarMiddle_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """match x:
    case [1, *y, 3]:
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
