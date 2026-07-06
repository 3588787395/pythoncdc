import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM12MatchMultiType_n(ExhaustiveTestCase):
    SOURCE_CODE = """match n:
    case int():
        pass
    case str():
        pass
    case float():
        pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
