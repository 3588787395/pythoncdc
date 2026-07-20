import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04ParenCmpChain(ExhaustiveTestCase):
    # 括号比较 false-positive 链式误判（(a==b) == (c==d)）
    SOURCE_CODE = """if (a == b) == (c == d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
