import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MatchSeqStar(ExhaustiveTestCase):
    # if 体内 match 序列模式带 star
    SOURCE_CODE = """if c:
    match s:
        case [a, *rest, b]:
            print(a, rest, b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
