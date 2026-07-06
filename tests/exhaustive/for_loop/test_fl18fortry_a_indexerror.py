import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL18ForTry_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(5):
    try:
        pass
    except IndexError:
        continue"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
