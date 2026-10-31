def f(rows, limit):
    out = []
    for row in rows:
        if len(row) > limit:
            raise ValueError("too wide")
        if len(row) >= 2:
            if not isinstance(row[1], str):
                raise ValueError("bad second")
        out.append(row)
    return out
