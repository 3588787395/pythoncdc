import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04DelNestedSubscr(ExhaustiveTestCase):
    # del 嵌套下标（del a[b][c]）
    SOURCE_CODE = """if c:
    del a[b][c]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
