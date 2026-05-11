import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry04TryExceptElse(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    process()
except Error:
    recover()
else:
    log_success()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
