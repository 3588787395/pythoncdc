import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM02MatchLiteralStr_a(ExhaustiveTestCase):
    SOURCE_CODE = """match a:
    case 'a':
        pass
    case 'b':
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
