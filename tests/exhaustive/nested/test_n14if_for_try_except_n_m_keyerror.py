import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN14If_For_Try_Except_n_m_KeyError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, condition):
    if condition:
        for item in data:
            try:
                n = item['key']
            except KeyError:
                n = 'missing'"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
