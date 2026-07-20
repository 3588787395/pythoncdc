import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11DictUnpackMixed(ExhaustiveTestCase):
    # if 体内 dict unpack 与普通 kv 混合 {**a, 1: 2, **b, 3: 4}
    SOURCE_CODE = """if c:
    x = {**a, 1: 2, **b, 3: 4}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
