import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile04Continue(ExhaustiveTestCase):
    SOURCE_CODE = """while i < 100:
    i += 1
    if i % 10 != 0:
        continue
    print(i)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
