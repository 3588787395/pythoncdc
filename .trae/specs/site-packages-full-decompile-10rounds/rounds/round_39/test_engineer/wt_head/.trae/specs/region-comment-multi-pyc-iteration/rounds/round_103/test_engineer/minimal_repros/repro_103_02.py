def check_value(x):
    if not x is not None:
        return 'none_or_zero'
    else:
        return 'has_value'

result = check_value(42)
