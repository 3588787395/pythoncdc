# round-2 r2v3 specimen (synthetic, minimal)
flag = 1
for i in range(3):
    if i:
        break
    if flag == 1:
        log('a')
    elif flag == -1:
        log('b')
    raise SystemExit
log('after')
