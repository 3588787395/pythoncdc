import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08TupleUnpackSubscrTarget(ExhaustiveTestCase):
    # if 体内 tuple unpack 含下标目标 a[0], b = c, d
    SOURCE_CODE = """if c:
    a[0], b = c, d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
