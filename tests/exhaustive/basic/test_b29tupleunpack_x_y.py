import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB29TupleUnpack_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """x, y = 1, 2"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
