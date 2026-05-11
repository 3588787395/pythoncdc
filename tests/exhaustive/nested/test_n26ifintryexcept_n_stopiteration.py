import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN26IfInTryExcept_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if n > 0:
        pass
except StopIteration:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
