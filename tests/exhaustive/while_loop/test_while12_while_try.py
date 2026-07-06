import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile12WhileTry(ExhaustiveTestCase):
    SOURCE_CODE = """while requests:
    req = requests.popleft()
    try:
        handle(req)
    except Exception:
        errors.append(req)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
