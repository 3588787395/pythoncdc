import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN26IfInTryExcept_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if x > 0:
        pass
except ValueError:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
