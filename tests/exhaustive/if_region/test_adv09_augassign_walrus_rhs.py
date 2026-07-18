import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09AugassignWalrusRhs(ExhaustiveTestCase):
    # if 体内 augassign 含 walrus 右值 a += (n := f())
    SOURCE_CODE = """if c:
    a += (n := f())"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
