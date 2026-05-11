import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry18BreakInTry(ExhaustiveTestCase):
    SOURCE_CODE = """for item in items:
    try:
        if stop(item):
            break
        process(item)
    except Error:
        skip(item)"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
