# F-EXCTABLE / negative control: try + except WITHOUT an else clause. Reading must
# stay identical to landed (no else may be invented).
def parse_strict(raw):
    try:
        text = str(raw).strip()
    except (TypeError, ValueError):
        text = ''
    return text
