import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE29IfInTry_StopIteration_n(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if n > 0:
        pass
except StopIteration:
    pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
