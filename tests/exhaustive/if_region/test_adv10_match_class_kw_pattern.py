import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MatchClassKwPattern(ExhaustiveTestCase):
    # if 体内 match 类模式带关键字参数
    SOURCE_CODE = """if c:
    match p:
        case Point(x=1, y=2):
            print(p)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
