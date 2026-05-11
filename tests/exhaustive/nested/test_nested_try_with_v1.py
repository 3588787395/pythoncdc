import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedTryWith_v1(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    with open('f') as f: y = f.read()
except:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
