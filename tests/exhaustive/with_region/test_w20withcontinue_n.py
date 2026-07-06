import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW20WithContinue_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    with open('f') as f:
        continue"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
