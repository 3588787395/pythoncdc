import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE21TryMultiExceptAs_StopIteration_ZeroDivisionError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    pass
except StopIteration as e1:
    pass
except ZeroDivisionError as e2:
    pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
