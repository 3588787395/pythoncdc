# Source Generated with Decompyle++ (Python version)
# File: rv9_02_b66_with_nest.pyc (Python 3.11)

__doc__ = """rv9_02: B66 boundary attacks (round9 re-review, 9.3).

Units:
  cont_in_with_nested_loop - continue inside nested loop hosted by with (cross-layer)
  cont_in_with_no_else     - with host, guard if has no else arm
  with_whole_body_pass     - with as entire loop body (false-trigger boundary)
  while_with_whole_body    - while True + with whole body (false-trigger boundary)
"""
def cont_in_with_nested_loop(xs, p, a):
    for x in xs:
        with open(p) as f:
            for y in f:
                if a(y):
                    continue
                use(y)
                continue
    return 8
def cont_in_with_no_else(xs, p, a):
    for x in xs:
        with open(p) as f:
            if a(f, x):
                continue
    return 9
def with_whole_body_pass(xs, p):
    for x in xs:
        with open(p) as f:
            pass
    return 14
def while_with_whole_body(p):
    while True:
        with open(p) as f:
            break
