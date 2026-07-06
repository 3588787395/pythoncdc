import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN24TryInTry_StopIteration_ZeroDivisionError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        pass
    except StopIteration:
        pass
except ZeroDivisionError:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
