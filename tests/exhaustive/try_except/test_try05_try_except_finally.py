import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry05TryExceptFinally(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    work()
except Error:
    fix()
else:
    commit()
finally:
    cleanup()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
