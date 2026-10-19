def s_b87c(rows):
    out = []
    try:
        for r in rows:
            try:
                for c in r:
                    out.append(c)
            finally:
                out.append(None)
    except ValueError:
        return []
    return out
