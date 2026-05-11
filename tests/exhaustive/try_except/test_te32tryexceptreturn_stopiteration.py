import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE32TryExceptReturn_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    try:
        return 1
    except StopIteration:
        return 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
