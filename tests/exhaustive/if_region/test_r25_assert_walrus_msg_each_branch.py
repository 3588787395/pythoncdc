import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AssertWalrusMsgEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        assert x < 100, (msg := f'value {x}')
        return msg
    elif x < 0:
        assert x > -100, (msg := f'value {x}')
        return msg
    else:
        return 'zero' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
