import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM25MatchReturn_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a):
    match a:
        case 1:
            return 1
        case _:
            return 0"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
