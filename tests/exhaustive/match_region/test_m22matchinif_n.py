import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM22MatchInIf_n(ExhaustiveTestCase):
    SOURCE_CODE = """if True:
    match n:
        case 1:
            pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
