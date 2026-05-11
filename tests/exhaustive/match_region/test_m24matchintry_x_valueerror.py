import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM24MatchInTry_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    match x:
        case 1:
            pass
except ValueError:
    pass"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
