import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5ForTryExceptBreakInExcept(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for i in r:
        try:
            do()
        except E:
            if i:
                break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
