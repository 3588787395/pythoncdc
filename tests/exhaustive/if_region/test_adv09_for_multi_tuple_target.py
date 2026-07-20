import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09ForMultiTupleTarget(ExhaustiveTestCase):
    # if 体内 for 多元 tuple 目标 for (a, b), (c, d) in pairs
    SOURCE_CODE = """if c:
    for (a, b), (c, d) in pairs:
        print(a, b, c, d)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
