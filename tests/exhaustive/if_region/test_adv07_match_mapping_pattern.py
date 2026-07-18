import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07MatchMappingPattern(ExhaustiveTestCase):
    # if 体内 match-case mapping 解构: case {"k": v}:
    SOURCE_CODE = """if c:
    match d:
        case {"k": v}:
            r = v
        case _:
            r = None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
