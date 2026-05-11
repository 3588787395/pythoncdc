import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL08ForDict_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(d):
    for k, v in d.items():
        n = k + v"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
