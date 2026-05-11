import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB14ExprCallNoArg_str(ExhaustiveTestCase):
    SOURCE_CODE = """str()"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
