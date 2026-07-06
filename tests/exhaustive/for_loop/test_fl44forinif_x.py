import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL44ForInIf_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    for i in range(5):
        x = x - 1
else:
    x = 0"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
