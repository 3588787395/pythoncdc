import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN25WithInWith_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """with open('a') as a:
    with open('b') as b:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
