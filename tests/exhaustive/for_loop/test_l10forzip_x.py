import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL10ForZip_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b):
    for x, y in zip(a, b):
        z = x + y"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
