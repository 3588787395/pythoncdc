import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile03Break(ExhaustiveTestCase):
    SOURCE_CODE = """while True:
    x = get_data()
    if x is None:
        break
    process(x)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
