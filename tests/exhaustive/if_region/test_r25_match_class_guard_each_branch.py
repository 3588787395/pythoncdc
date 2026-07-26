import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25MatchClassGuardEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        match x:
            case int(v) if v > 100:
                return 'big int'
            case _:
                return 'small int'
    elif x < 0:
        return 'neg'
    else:
        return 'zero' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
