import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile20ComplexStateMachine(ExhaustiveTestCase):
    SOURCE_CODE = """state = 'idle'
while state != 'done':
    if state == 'idle':
        event = wait_event()
        if event:
            state = 'processing'
    elif state == 'processing':
        result = process(event)
        if result.ok:
            state = 'done'
        else:
            state = 'error'
    else:
        log_error(result)
        state = 'idle'"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
