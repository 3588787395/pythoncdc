import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF09IfContinue_a(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(10):
    if a > 5:
        continue"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
