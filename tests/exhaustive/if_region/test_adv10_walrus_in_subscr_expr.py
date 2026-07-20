import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10WalrusInSubscrExpr(ExhaustiveTestCase):
    # if 体内 walrus 在下标表达式 x[(y := f())]
    SOURCE_CODE = """if c:
    x = d[(y := f())]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
