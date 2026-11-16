# g2c REAL46-031 side case (LIVE in current tree): or-of-two-ands ternary is
# split into a guard `if not (A and B):` whose body swallows the rest of the module.
import sys
OLD = 'old'
NEW = 'new'
V = OLD if (sys.flags and sys.version_info > (3, 0)) or (sys.maxsize > 0 and sys.argv) else NEW
print('V =', V)
