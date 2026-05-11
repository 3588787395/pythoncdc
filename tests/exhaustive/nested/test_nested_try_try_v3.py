import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedTryTry_v3(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        q = 1
    except:
        q = 2
except:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
