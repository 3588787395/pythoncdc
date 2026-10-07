# Source Generated with Decompyle++ (Python version)
# File: r6_g4_reloc_spec.pyc (Python 3.11)

def r6_g4_reloc_spec(rows, seen):
    for row in rows:
        if row in seen:
            log('dup %s' % row)
            return None
        else:
            warn('bad %s' % row)
            return None
    return rows
