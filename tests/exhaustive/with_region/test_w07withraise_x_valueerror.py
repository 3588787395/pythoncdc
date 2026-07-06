import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW07WithRaise_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as x:
    raise ValueError"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
