import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry09RaiseInTry(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if bad:
        raise ValueError("bad")
    process()
except ValueError:
    handle()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
