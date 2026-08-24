# R101-Pattern-C-rich: for > while > if/elif/else with DOUBLE break in elif,
# followed by post-chain statements inside the while (closer to
# change_his_to_backward real nesting).


def process(rows, empty_at):
    out = []
    acc = None
    for tag in ('a', 'b'):
        i = 0
        while i < len(rows):
            cur = rows[i]
            if cur == 'stop':
                break
            elif i == empty_at:
                break
                break
            elif cur:
                out.append(cur.upper())
            else:
                out.append(cur)
            if acc != i:
                acc = i
            i += 1
        if acc is not None and len(out) > 0:
            acc = -1
    return out


def run(rows, e):
    return process(rows, e)
