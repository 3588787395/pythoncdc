import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF46Ifinifelse_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    n = 1
else:
    if n < -5:
        n = -5"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
