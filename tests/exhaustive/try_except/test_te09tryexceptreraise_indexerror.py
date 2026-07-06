import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE09TryExceptReraise_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    pass
except IndexError:
    raise"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
