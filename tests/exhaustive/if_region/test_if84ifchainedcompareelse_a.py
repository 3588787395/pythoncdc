import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF84Ifchainedcompareelse_a(ExhaustiveTestCase):
    SOURCE_CODE = """if 0 < a < 10:
    a = a + 1
else:
    a = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
