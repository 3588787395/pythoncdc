"""m05: module-level match with nested match."""
MODE = {'op': 'run'}
match MODE:
    case {'op': op} if op:
        for k in ('a', 'b'):
            match k:
                case 'a':
                    FIRST = k
                case _:
                    OTHER = k
    case _:
        MODE = None
