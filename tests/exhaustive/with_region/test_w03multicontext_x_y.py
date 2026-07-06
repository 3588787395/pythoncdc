import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW03MultiContext_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """with open('a') as x, open('b') as y:
    pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
