"""m06: module-level for/while with else clauses and loop control."""
TOTAL = 0
for i in range(5):
    if i == 3:
        continue
    if i == 4:
        break
    TOTAL += i
else:
    TOTAL = -1
i = 0
while i < 3:
    i += 1
    for j in range(i):
        if j:
            continue
        else:
            break
    else:
        TOTAL += j
else:
    TOTAL += 100
