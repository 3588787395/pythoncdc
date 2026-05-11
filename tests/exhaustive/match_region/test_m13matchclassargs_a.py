import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM13MatchClassArgs_a(ExhaustiveTestCase):
    SOURCE_CODE = """match a:
    case int(1):
        pass
    case int(2):
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
