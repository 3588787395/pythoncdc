import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL11ForEnumerate_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    for i, item in enumerate(items):
        x = i + item"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
