import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor13MultiStmt(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(3):
    a = i
    b = i * 2
    c = a + b"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
