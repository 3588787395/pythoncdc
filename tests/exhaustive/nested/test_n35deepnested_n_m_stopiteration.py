import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN35DeepNested_n_m_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    for m in range(3):
        try:
            if m == 1:
                pass
        except StopIteration:
            pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
