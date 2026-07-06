import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN17For_If_Elif_Else_n_m_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(values):
    for v in values:
        if v > 100:
            n = v + 1
        elif v < 0:
            m = -v
        else:
            x = v * v"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
