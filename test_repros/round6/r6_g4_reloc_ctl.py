def r6_g4_reloc_ctl(rows, seen):
    for row in rows:
        if row in seen:
            log('dup %s' % row)
            return None
        warn('bad %s' % row)
    return rows
