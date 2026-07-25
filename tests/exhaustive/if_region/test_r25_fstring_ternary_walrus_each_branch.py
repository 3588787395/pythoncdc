import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25FstringTernaryWalrusEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        return f"{(y := x) if x > 0 else 0} is positive"
    elif x < 0:
        return f"{(y := -x) if x < 0 else 0} is negative"
    else:
        return f"{(y := x)} is zero" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
