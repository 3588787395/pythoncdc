import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE14TryExceptTuple_ValueError_TypeError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    pass
except (ValueError, TypeError):
    pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
