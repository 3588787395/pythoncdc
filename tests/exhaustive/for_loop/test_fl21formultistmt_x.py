import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL21ForMultiStmt_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(5):
    x += 1
    x *= 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
