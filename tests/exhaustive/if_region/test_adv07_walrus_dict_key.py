import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07WalrusDictKey(ExhaustiveTestCase):
    # if 体内 walrus 作 dict 字面量 key: {(n := f()): v}
    SOURCE_CODE = """if c:
    r = {(n := f()): v}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
