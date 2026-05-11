import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF90Ifelifelseraise_x_RuntimeError(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    pass
elif x == 0:
    raise RuntimeError
else:
    raise KeyError"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
