import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25WalrusWhileCondInIfBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(it, mode):
    if mode == 'a':
        while (x := next(it, None)) is not None:
            if x > 0:
                process(x)
            else:
                break
        return 'done'
    elif mode == 'b':
        return 'b'
    else:
        return 'c' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
