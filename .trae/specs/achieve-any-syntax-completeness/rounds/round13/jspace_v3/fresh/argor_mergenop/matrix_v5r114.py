# rr-v5r114 [v114-ARGOR]+[v114-MERGENOP] 变体矩阵案源（与 r114_regress.py 同源）
# 功效案 4：E1（ARGOR 方法形）/E2（MERGENOP 三元+裸字符串）/E4（ARGOR 单实参）/E8（ARGOR 后缀二元）
# 控制案 7：E3/E7（HEAD 已正确形）/C1/C2/C3/C4/C5；未领边界 1：E6（相邻 NOP 对 [Round 33] 既有排除域）
CASES = {
    # ---- 功效案 ----
    'E1_argor_method': '''import re


class Version:
    def __init__(self, version, match):
        self._pre = _parse_letter_version(match.group("pre_l"), match.group("pre_n"))
        self._post = _parse_letter_version(
            match.group("post_l"), match.group("post_n1") or match.group("post_n2")
        )
        self._dev = _parse_letter_version(match.group("dev_l"), match.group("dev_n"))
        return
''',
    'E2_mergenop_ternary': '''import re
import sys

if sys.version_info >= (3, 9):
    _flag = "new"
else:
    _flag = "old"

_OLD = "old-pattern"
_NEW = "new-pattern"
VERSION_PATTERN = (
    _OLD
    if (sys.implementation.name == "cpython" and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == "pypy" and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else _NEW
)
"""
A string containing the regular expression used to match a valid version.
:meta hide-value:
"""
_LOCAL_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE | re.ASCII)
''',
    'E3_argor_simplename': '''def run(match):
    pre = _parse_letter_version(match.group("pre_l"), match.group("pre_n"))
    post = _parse_letter_version(
        match.group("post_l"), match.group("post_n1") or match.group("post_n2")
    )
    dev = _parse_letter_version(match.group("dev_l"), match.group("dev_n"))
    return pre, post, dev
''',
    'E4_argor_single_arg': '''class C:
    def m(self, v):
        self.x = _wrap(v or "d")
        return self.x
''',
    'E6_mergenop_two_orphans': '''import sys

if sys.version_info >= (3, 9):
    _flag = 1

X = "a" if sys.platform else "b"
"""
first orphan doc
"""
"""
second orphan doc
"""
Y = "z"
''',
    'E7_mergenop_before_for': '''import sys

if sys.version_info >= (3, 9):
    _flag = 1

N = 3 if sys.platform else 4
"""
doc between
"""
for _i in range(N):
    print(_i)
''',
    'E8_argor_postfix_binop': '''class C:
    def m(self, v):
        self.x = _wrap(v or "d") + 1
        return self.x
''',
    # ---- 控制案 ----
    'C1_no_ternary_orphan': '''import re

VERSION_PATTERN = "abc"
"""
A string docstring here.
"""
_LOCAL_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
''',
    'C2_boolop_orphan': '''import sys

if sys.version_info >= (3, 9):
    _flag = 1

_X = "a"
_Y = "b"
VAL = _X or _Y
"""
docstring between statements
"""
OTHER = "z"
''',
    'C3_ternary_no_orphan': '''import sys

if sys.version_info >= (3, 9):
    _flag = 1

X = "a" if sys.platform else "b"
Y = X + "!"
''',
    'C4_r67_plain': '''class C:
    def m(self, v, d):
        self.x = v or d
        return self.x
''',
    'C5_no_boolop_call': '''def run(m):
    pre = _parse_letter_version(m.group("pre_l"), m.group("pre_n"))
    return pre
''',
}
