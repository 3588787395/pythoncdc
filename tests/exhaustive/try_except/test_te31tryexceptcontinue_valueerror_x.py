import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE31TryExceptContinue_ValueError_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    try:
        if x == 5:
            continue
    except ValueError:
        pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
