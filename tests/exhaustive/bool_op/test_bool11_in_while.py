import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBool11InWhile(ExhaustiveTestCase):
    SOURCE_CODE = """while not done and has_data():
    process()"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
