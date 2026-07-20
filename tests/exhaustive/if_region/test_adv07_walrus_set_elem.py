import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07WalrusSetElem(ExhaustiveTestCase):
    # if 体内 walrus 作 set 字面量元素: {(n := f()), m}
    SOURCE_CODE = """if c:
    r = {(n := f()), m}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
