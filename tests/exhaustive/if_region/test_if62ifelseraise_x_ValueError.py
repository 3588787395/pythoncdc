import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF62Ifelseraise_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    x = 1
else:
    raise ValueError"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
