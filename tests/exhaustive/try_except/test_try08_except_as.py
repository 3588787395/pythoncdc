import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry08ExceptAs(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    op()
except ValueError as e:
    log(e)"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
