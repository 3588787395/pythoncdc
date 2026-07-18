import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07MatchOrPattern(ExhaustiveTestCase):
    # if 体内 match-case or 模式: case 1 | 2:
    SOURCE_CODE = """if c:
    match x:
        case 1 | 2:
            r = 'low'
        case _:
            r = 'other'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
