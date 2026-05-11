import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF84Ifchainedcompareelse_x(ExhaustiveTestCase):
    SOURCE_CODE = """if 0 < x < 10:
    x = x + 1
else:
    x = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
