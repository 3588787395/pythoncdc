def test():
    try:
        x = int('abc')
    except ValueError as e:
        return str(type(e).__name__)
    return 'no_error'
