def chain(x, seq):
    if x == 1:
        while x > 0: x -= 1            # While
        for i in seq: pass             # For
    elif x == 2:
        try:
            pass
        except Exception: pass         # Try
        match x:
            case 1: pass               # Match
    elif x == 3:
        if x > 2:
            while True:
                if x: break            # Break
                continue               # Continue
    else:
        pass
