import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE01TryExcept_ValueError_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    try:
        int(x)
    except ValueError:
        x = "0\""""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
