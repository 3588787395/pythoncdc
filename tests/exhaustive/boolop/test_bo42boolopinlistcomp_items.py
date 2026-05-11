import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO42BoolOpInListComp(ExhaustiveTestCase):
    SOURCE_CODE = """[x for x in items if x > 0 and x < 100]"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
