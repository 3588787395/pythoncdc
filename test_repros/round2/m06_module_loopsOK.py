# Source Generated with Decompyle++ (Python version)
# File: m06_module_loops.pyc (Python 3.11)

__doc__ = 'm06: module-level for/while with else clauses and loop control.'
TOTAL = 0
for i in range(5):
    if i == 3:
        continue
    elif i == 4:
        break
    else:
        TOTAL += i
        continue
else:
    TOTAL = -1
i = 0
while i < 3:
    i += 1
    for j in range(i):
        if j:
            continue
    else:
        TOTAL += j
    TOTAL += 100
