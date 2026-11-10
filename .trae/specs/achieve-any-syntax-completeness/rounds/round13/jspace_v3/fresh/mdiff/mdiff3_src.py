def gen(line_iterator):
    fromlines, tolines = [], []
    while True:
        while (len(fromlines) == 0 or len(tolines) == 0):
            try:
                from_line, to_line, found_diff = next(line_iterator)
            except StopIteration:
                return
            if from_line is not None:
                fromlines.append((from_line, found_diff))
            if to_line is not None:
                tolines.append((to_line, found_diff))
        from_line, fromDiff = fromlines.pop(0)
        to_line, to_diff = tolines.pop(0)
        yield (from_line, to_line, fromDiff or to_diff)
