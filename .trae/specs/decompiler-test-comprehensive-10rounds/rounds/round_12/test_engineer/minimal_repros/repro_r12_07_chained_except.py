# R12 MinRepro 07: chained except handlers

def parse_value(s):
    try:
        return int(s)
    except TypeError:
        return 0
    except ValueError:
        return -1
    finally:
        print(f'parsed {s}')
