import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL07ForEnumerate_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """for x, y in enumerate([1, 2, 3]):
    pass"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
