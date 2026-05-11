import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF09IfContinue_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    if n > 5:
        continue"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
