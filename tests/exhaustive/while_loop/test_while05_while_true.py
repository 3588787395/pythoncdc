import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile05WhileTrue(ExhaustiveTestCase):
    SOURCE_CODE = """while True:
    do_something()
    if done:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
