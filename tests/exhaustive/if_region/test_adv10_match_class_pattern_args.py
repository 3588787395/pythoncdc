import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MatchClassPatternArgs(ExhaustiveTestCase):
    # if 体内 match 语句使用类模式带位置参数
    SOURCE_CODE = """if c:
    match p:
        case Point(x, y):
            print(x, y)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
