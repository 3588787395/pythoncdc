import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF67Ifdoublenested_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    if a > 10:
        if a > 100:
            a = 100"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
