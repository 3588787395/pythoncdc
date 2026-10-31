def f(grid):
    hits = 0
    r = 0
    while r < len(grid):
        row = grid[r]
        if not row:
            r += 1
            continue
        c = 0
        while c < len(row):
            v = row[c]
            if v is None:
                c += 1
                continue
            hits += v
            c += 1
        r += 1
    return hits
