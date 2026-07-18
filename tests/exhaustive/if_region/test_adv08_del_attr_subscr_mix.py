import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08DelAttrSubscrMix(ExhaustiveTestCase):
    # if 体内 del 属性和下标混合 del a.b, c.d[e]
    SOURCE_CODE = """if c:
    del a.b, c.d[e]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
