import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10WalrusChainLeftCond(ExhaustiveTestCase):
    # if 条件中海象在链式比较左值 (x:=f()) > 0 and (y:=g()) > 0
    SOURCE_CODE = """if (x := f()) > 0 and (y := g()) > 0:
    z = x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
