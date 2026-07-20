import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08NestedWalrusSubscr(ExhaustiveTestCase):
    # if 条件含嵌套下标中的 walrus d[a[(n := f())]]
    SOURCE_CODE = """if c:
    r = d[a[(n := f())]]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
