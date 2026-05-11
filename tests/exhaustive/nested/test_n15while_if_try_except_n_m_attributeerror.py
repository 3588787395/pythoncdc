import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN15While_If_Try_Except_n_m_AttributeError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(objects, max_count):
    cnt = 0
    while cnt < max_count:
        if objects[cnt] is not None:
            try:
                n = objects[cnt].value
            except AttributeError:
                n = 0
        cnt += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
