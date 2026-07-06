import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_Try_Try_If_v1(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        if z > 0:
            z -= 1
    except Exception:
        pass
except Exception:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
