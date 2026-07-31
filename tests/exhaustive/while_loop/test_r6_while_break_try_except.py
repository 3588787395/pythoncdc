import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileBreakTryExcept(ExhaustiveTestCase):
    # CTRL: while + try/except + break == known test_wl30whilebreakintry family
    # (except-cleanup pollution). Filed for traceability; NOT counted as a
    # new LOOP defect (Round_05 deferred Bug #10).
    SOURCE_CODE = """n = 0
while n < 10:
    try:
        n += 1
        if n > 5:
            break
    except Exception:
        n = 0"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
