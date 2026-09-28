# synth a03s -- nested if/else inside top-level if, shared tail statement
# after the inner chain, function-tail assignment after the outer if.
def synth_a03s_nested_else_shared_tail(a, b, c, d, log):
    out = {}
    if a and b > c:
        if not b:
            if c <= d:
                out['x'] = 1
            else:
                out['x'] = 2
        else:
            out['x'] = 3
        return out
    out = get_tail(a, b, c, d, log)
    return out


def get_tail(a, b, c, d, log):
    return {'t': (a, b, c, d)}
