import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11WalrusCompIfFilter(ExhaustiveTestCase):
    # if 体内 list comprehension 中 if 过滤条件含 walrus
    SOURCE_CODE = """if c:
    r = [x for x in y if (n := x) > 0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
