import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM106MatchGuardBoolOp(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    match x:
        case n if n > 0 and n < 100:
            return "small"
        case n if n >= 100 or n < -10:
            return "large"
        case _:
            return "other"
"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
