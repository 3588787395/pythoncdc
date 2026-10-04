# Source Generated with Decompyle++ (Python version)
# File: rv9_01_b68_nonfin_tail.pyc (Python 3.11)

__doc__ = """rv9_01: B68 boundary attacks (round9 re-review, 9.3).

Units:
  nonfin_tail_break   - non-empty finally + trailing break (gate must refuse release)
  nonfin_tail_cont    - non-empty finally + trailing continue in while host
  emptyfin_ifelse_ret - empty finally + trailing if/else dual-arm return
  emptyfin_in_if      - empty finally nested inside if host
"""
def nonfin_tail_break(xs, a):
    for x in xs:
        try:
            f(x)
        finally:
            g(x)
        if a(x):
            break
    return 1
def nonfin_tail_cont(xs, a):
    while xs:
        try:
            f(xs)
        finally:
            g(xs)
        if a(1):
            continue
        xs.pop()
    return 2
def emptyfin_ifelse_ret(a):
    try:
        pass
    finally:
        pass
    if a:
        return 3
    else:
        return 4
def emptyfin_in_if(a):
    if a:
        try:
            pass
        finally:
            pass
    else:
        return 7
