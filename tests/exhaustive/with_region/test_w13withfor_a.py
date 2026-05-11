import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW13WithFor_a(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as a:
    for i in range(3):
        pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
