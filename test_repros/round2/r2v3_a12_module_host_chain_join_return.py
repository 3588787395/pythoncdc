# round-2 r2v3 specimen (synthetic, minimal)
flag = poll()
redata = get()
if flag == 1:
    log('a')
elif flag == -1:
    log('b')
return_if_true(redata)
log('after')
