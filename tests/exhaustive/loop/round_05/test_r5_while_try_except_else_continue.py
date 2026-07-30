import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5WhileTryExceptElseContinue(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        try:
            do()
        except E:
            if b:
                continue
        else:
            x = 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
