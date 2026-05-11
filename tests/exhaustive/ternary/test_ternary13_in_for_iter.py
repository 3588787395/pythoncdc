import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary13InForIter(ExhaustiveTestCase):
    SOURCE_CODE = """for x in (list_a if use_a else list_b):
    pass"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
