import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09IfNotWalrus(ExhaustiveTestCase):
    # if 条件中的海象 + not 组合 if not (x := f()):
    SOURCE_CODE = """if not (x := f()):
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
