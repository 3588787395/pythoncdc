# Source Generated with Decompyle++ (Python version)
# File: m05_module_match.pyc (Python 3.11)

__doc__ = 'm05: module-level match with nested match.'
MODE = {'op': 'run'}
match MODE:
    case {'op': op}:
        for k in ('a', 'b'):
            match k:
                case 'a':
                    FIRST = k
                    continue
                case _:
                    OTHER = k
    case _:
        MODE = None
