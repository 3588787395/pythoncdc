import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW05WithTry_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    with open('f') as x:
        pass
except ValueError:
    pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
