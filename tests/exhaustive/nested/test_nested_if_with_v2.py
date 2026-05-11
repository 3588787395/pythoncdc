import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedIfWith_v2(ExhaustiveTestCase):
    SOURCE_CODE = """if a:
    with open('f') as f: b = f.read()"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
