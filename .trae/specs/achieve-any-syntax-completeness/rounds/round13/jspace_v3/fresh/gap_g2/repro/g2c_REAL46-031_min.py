# g2c REAL46-031 min: or-of-ands conditional expression feeding a str concat.
import sys
OLD = 'old'
NEW = 'new'
VERSION_PATTERN = (
    OLD
    if (sys.implementation.name == 'cpython' and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == 'pypy' and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else NEW
)
print('\\s*' + VERSION_PATTERN + '\\s*')
