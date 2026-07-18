import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07AttrSubscrChain(ExhaustiveTestCase):
    # if 体内属性链 + 下标混合: a.b[c].d[e]
    SOURCE_CODE = """if c:
    r = a.b[c].d[e]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
