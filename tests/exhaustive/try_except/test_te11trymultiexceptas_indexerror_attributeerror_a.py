import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE11TryMultiExceptAs_IndexError_AttributeError_a(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    pass
except IndexError as a:
    pass
except AttributeError:
    pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
