import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ForTryExceptBreakContinue(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for i in items:
        try:
            if i == 0:
                break
        except ValueError:
            continue
    return i"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
