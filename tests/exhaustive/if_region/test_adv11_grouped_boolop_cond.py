import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11GroupedBoolopCond(ExhaustiveTestCase):
    # if 条件中分组 boolop if (a or b) and (c or d):
    SOURCE_CODE = """if (a or b) and (c or d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
