import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry10RaiseInExcept(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    work()
except Error:
    log_error()
    raise"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
