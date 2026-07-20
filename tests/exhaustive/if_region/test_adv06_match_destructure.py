import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06MatchDestructure(ExhaustiveTestCase):
    # if 体内 match-case 带解构
    SOURCE_CODE = """if c:
    match x:
        case [a, b, *rest]:
            y = a + b
        case _:
            y = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
