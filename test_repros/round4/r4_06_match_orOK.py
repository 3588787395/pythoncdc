# Source Generated with Decompyle++ (Python version)
# File: r4_06_match_or.pyc (Python 3.11)

def match_or_values(x):
    """Attack 1: or-pattern over literal values."""
    match x:
        case 1 | 2 | 3:
            return 'small'
        case 4 | 5:
            return 'mid'
        case _:
            return 'big'
def match_or_str(x):
    """Attack 2: or-pattern over strings."""
    match x:
        case 'yes' | 'y' | 'ok':
            return True
        case 'no' | 'n':
            return False
        case _:
            pass
def match_or_sequence(seq):
    """Attack 3: or-pattern over sequence shapes."""
    match seq:
        case [0, 0] | [1, 1]:
            return 'diagonal'
        case [0, y] | [y, 0]:
            return ('axis', y)
        case _:
            return 'elsewhere'
def match_or_mixed_types(x):
    """Attack 4: or-pattern mixing int and str."""
    match x:
        case 0 | 'zero':
            return 0
        case 1 | 'one':
            return 1
        case _:
            return -1
def match_or_capture_body(x):
    """Attack 5: or-pattern combined with guard and body work."""
    match x:
        case 1 | 2 | 3 | 4:
            for i in range(x):
                total.append(i)
            return total
        case 5 | 6:
            total.append(x * 10)
        case _:
            total = None
