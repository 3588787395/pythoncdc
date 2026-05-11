import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN27ForInTryExcept_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    for x in range(3):
        pass
except ValueError:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
