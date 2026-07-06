import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary10AsDefault(ExhaustiveTestCase):
    SOURCE_CODE = """def fn(x, y=DEFAULT if FLAG else ALT):
    pass"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
