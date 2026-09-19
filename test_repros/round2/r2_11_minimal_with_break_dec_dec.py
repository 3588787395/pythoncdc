# Source Generated with Decompyle++ (Python version)
# File: r2_11_minimal_with_break_dec.pyc (Python 3.11)

__doc__ = """Repro (bonus, minimal): while + try + with + break mangling.

Smallest shape sharing the r2_01 root-cause family: a `break` inside
a with-body that sits inside a try inside a while loop. Unlike the
full set_trade_status skeleton this does NOT collapse to `pass`, but
the decompiled loop is structurally wrong: the __exit__ cleanup call
gets emitted at the wrong place (orig LOAD_CONST(None) vs decomp
CALL(2) at the tail), shifting every subsequent instruction.

This is the 12-instruction core of the set_trade_status collapse:
  while cond:
      try:
          with ctx():
              work()
              break
      except BaseException:
          count += 1
"""
def ctx(p):
    return p
def f(path):
    count = 1
    while count <= 3:
        try:
            with ctx(path):
                data = path.upper()
        except BaseException:
            count += 1
    return count
