import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry13ForTry(ExhaustiveTestCase):
    SOURCE_CODE = """for item in items:
    try:
        process(item)
    except SkipError:
        continue"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
