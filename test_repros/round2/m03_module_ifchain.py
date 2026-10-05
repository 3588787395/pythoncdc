"""m03: module-level if/elif/else chain with deep arms."""
X = 3
if X == 1:
    A = 1
elif X == 2:
    A = 2
    for i in range(2):
        if i:
            while X:
                try:
                    X -= 1
                    break
                finally:
                    X = X
        else:
            A = i
elif X == 3:
    A = 3
    with _CM() as B:
        if B:
            for k in range(1):
                A += k
else:
    A = 4
    while X:
        if X:
            X -= 1
        else:
            break
