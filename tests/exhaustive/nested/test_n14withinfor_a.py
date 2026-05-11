import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN14WithInFor_a(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(3):
    with open('f') as f:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
