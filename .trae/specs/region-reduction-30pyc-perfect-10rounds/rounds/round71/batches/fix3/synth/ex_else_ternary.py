# F-EXCTABLE / positive: try + except + else, else clause holds an expression child
# (ternary). The try body must NOT swallow the else clause.
def parse_thing(raw):
    try:
        text = str(raw).strip()
    except (TypeError, ValueError):
        text = ''
    else:
        label = 'ok' if text else 'empty'
        text = label
    return text
