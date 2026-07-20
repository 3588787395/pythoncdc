import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MatchMappingRest(ExhaustiveTestCase):
    # if 体内 match 映射模式带 rest
    SOURCE_CODE = """if c:
    match d:
        case {"k": v, **rest}:
            print(v, rest)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
