import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF62Ifelseraise_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    n = 1
else:
    raise StopIteration"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
