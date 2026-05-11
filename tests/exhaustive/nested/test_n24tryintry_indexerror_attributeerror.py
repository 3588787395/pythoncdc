import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN24TryInTry_IndexError_AttributeError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        pass
    except IndexError:
        pass
except AttributeError:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
