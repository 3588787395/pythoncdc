import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2ForIterWalrus(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for x in (n := g()):
        y = x"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
