import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile19BreakContinueCombo(ExhaustiveTestCase):
    SOURCE_CODE = """while processing:
    event = get_event()
    if event is None:
        continue
    if event.type == STOP:
        break
    handle(event)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
