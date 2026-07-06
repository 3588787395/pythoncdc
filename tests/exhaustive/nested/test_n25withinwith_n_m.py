import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN25WithInWith_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """with open('a') as n:
    with open('b') as m:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
