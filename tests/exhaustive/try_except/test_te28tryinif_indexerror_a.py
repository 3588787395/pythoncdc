import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE28TryInIf_IndexError_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    try:
        pass
    except IndexError:
        pass"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
