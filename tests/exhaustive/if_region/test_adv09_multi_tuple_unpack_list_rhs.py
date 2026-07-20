import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09MultiTupleUnpackListRhs(ExhaustiveTestCase):
    # if 体内 tuple unpack 含 list literal 右值 (a, b), (c, d) = [(1, 2), (3, 4)]
    SOURCE_CODE = """if c:
    (a, b), (c, d) = pairs"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
