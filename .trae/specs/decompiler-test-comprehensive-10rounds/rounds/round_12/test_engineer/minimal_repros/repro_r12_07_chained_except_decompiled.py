def parse_value(s):
    try:
        int(s)
    except TypeError:
        print(f'parsed {s}')
        return 0
        print(f'parsed {s}')
        return -1
    except ValueError:
        pass
    else:
        return print(f'parsed {s}')
    finally:
        print(f'parsed {s}')
