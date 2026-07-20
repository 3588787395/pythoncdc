import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11MultiTargetMixedUnpack(ExhaustiveTestCase):
    # if 体内多目标元组解包 a, b = c = d, e
    SOURCE_CODE = """if c:
    a, b = c = d, e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
