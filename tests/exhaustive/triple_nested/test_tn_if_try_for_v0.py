import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_If_Try_For_v0(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    try:
        for k in range(3):
            pass
    except Exception:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
