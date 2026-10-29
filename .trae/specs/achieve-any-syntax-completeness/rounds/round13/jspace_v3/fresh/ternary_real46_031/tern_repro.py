import sys
_VERSION_PATTERN_OLD = 'old'
_VERSION_PATTERN = 'new'
VERSION_PATTERN = (
    _VERSION_PATTERN_OLD
    if (sys.implementation.name == "cpython" and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == "pypy" and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else _VERSION_PATTERN
)
print('VP', type(VERSION_PATTERN).__name__, VERSION_PATTERN)
