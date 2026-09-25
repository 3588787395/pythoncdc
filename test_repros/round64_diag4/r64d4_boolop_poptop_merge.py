"""R64-D4 repro B: a statement-level BoolOp whose merge block starts with POP_TOP.

Mirrors site-packages/fly/logger.pyc :: Backtest.logging_process original line 84
(``thread_event.is_set() or thread_event.set()``).  The BoolOp expression statement
compiles to ``... CALL / JUMP_IF_TRUE_OR_POP / CALL / <merge: POP_TOP>`` and that POP_TOP
is the first instruction of the merge block that also holds the next statement
``info = self.receiver.recv()``.  _generate_boolop_impl splices the merge block into the
assignment value, so the BoolOp statement itself is never emitted as a statement.

Landed arm:  `ev.is_set() or ev.set()` missing -> official 3/4, strict seq_len short by 8.
Arm cand_r64d4_b_boolop_poptop_stmt: recovered -> official 4/4.
"""

from queue import Queue
from threading import Event


class Runner:
    def logging_process(self, receiver):
        write_queue = Queue()
        thread_event = Event()
        info = receiver.recv()
        while info:
            try:
                write_queue.put(info)
                thread_event.is_set() or thread_event.set()
                info = receiver.recv()
            except BaseException as e:
                self.status = False
