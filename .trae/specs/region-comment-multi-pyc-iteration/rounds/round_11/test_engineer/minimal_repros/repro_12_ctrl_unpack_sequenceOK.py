# Source Generated with Decompyle++ (Python version)
# File: repro_12_ctrl_unpack_sequence.pyc (Python 3.11)

__doc__ = """[R11 repro_12] CTRL: UNPACK_SEQUENCE-based tuple unpack (literal RHS).

`a, b = 1, 2` at module scope compiles with UNPACK_SEQUENCE because the
RHS is a constant tuple.  Pattern C2 detection must NOT fire (guard:
no UNPACK_SEQUENCE in value instrs).  Existing UNPACK_SEQUENCE path
handles this.
"""
a, b = 1, 2
