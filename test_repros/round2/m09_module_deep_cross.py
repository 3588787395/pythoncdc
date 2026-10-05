"""m09: module root depth-7 cross (with/try/for/if/while/match)."""
with _A() as a:
    try:
        for i in range(2):
            if i:
                while i:
                    match i:
                        case 1:
                            RES = 'one'
                        case _:
                            RES = 'other'
    finally:
        FIN = 0
