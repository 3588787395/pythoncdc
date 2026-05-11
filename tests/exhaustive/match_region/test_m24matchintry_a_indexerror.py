import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM24MatchInTry_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    match a:
        case 1:
            pass
except IndexError:
    pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
