def r6_g4_reloc_spec(rows, seen):
    for row in rows:
        if row in seen:
            log('dup %s' % row)
            return None
        warn('bad %s' % row)
        return None
    return rows
