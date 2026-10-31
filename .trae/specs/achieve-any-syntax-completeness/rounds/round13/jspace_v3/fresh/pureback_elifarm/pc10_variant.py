def f(grid):
    hits = []
    for row in grid:
        if not row:
            continue
        elif len(row) >= 2:
            if row[0] > row[1]:
                hits.append(row)
                break
    return hits
