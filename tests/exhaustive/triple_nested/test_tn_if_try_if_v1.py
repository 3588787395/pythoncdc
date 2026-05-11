import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_If_Try_If_v1(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    try:
        if z > 0:
            z -= 1
    except Exception:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
