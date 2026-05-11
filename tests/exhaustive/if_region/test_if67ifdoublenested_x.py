import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF67Ifdoublenested_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    if x > 10:
        if x > 100:
            x = 100"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
