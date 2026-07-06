import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN34ForWhileIf_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(5):
    while b > 0:
        if b > 2:
            b -= 1
        else:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
