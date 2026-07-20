import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11MultiTargetUnpack(ExhaustiveTestCase):
    # if 体内多目标元组解包 a, b = e, f = g, h
    SOURCE_CODE = """if c:
    a, b = e, f = g, h"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
