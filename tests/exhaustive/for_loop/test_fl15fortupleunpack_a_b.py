import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL15ForTupleUnpack_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """for a, b in [(1, 2), (3, 4)]:
    pass"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
