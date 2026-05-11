import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM26MatchAssign_a(ExhaustiveTestCase):
    SOURCE_CODE = """match a:
    case 1:
        x = 1
    case _:
        x = 0"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
