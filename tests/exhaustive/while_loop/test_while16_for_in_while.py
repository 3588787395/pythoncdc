import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile16ForInWhile(ExhaustiveTestCase):
    SOURCE_CODE = """while batch := get_batch():
    for item in batch:
        process(item)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
