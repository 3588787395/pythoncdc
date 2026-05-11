import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile18WithInWhile(ExhaustiveTestCase):
    SOURCE_CODE = """while has_more():
    with open(next_file()) as f:
        content = f.read()
        store(content)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
