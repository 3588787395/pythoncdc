import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE31TryExceptContinue_StopIteration_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    try:
        if n == 5:
            continue
    except StopIteration:
        pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
