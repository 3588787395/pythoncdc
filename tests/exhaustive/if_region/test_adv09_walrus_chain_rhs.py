import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09WalrusChainRhs(ExhaustiveTestCase):
    # if 体内 walrus 在比较链右值 x = (y := f()) > 0
    SOURCE_CODE = """if c:
    x = (y := f()) > 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
