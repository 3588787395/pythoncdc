import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL21ForMultiStmt_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(5):
    n += 1
    n *= 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
