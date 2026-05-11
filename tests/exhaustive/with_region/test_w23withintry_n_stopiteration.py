import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW23WithInTry_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    with open('f') as n:
        pass
except StopIteration:
    pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
