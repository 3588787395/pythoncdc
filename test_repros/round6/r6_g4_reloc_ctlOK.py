# Source Generated with Decompyle++ (Python version)
# File: r6_g4_reloc_ctl.pyc (Python 3.11)

def r6_g4_reloc_ctl(rows, seen):
    for row in rows:
        if row in seen:
            log('dup %s' % row)
            return None
        warn('bad %s' % row)
    return rows
