import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06WalrusOutsideComp(ExhaustiveTestCase):
    # if 体内 walrus 在表达式语句中 (n := f())
    SOURCE_CODE = """if c:
    (n := f())
    (m := g())
    r = n + m"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
