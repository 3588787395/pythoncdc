# Source Generated with Decompyle++ (Python version)
# File: repro.pyc (Python 3.11)

import sys
OLD = 'old'
NEW = 'new'
V = OLD if sys.flags and sys.version_info > (3, 0) or sys.maxsize > 0 and sys.argv else NEW
print('V =', V)
