import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN03ForInIf_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    for y in range(x):
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
