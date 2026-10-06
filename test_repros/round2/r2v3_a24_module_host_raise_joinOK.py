# Source Generated with Decompyle++ (Python version)
# File: r2v3_a24_module_host_raise_join.pyc (Python 3.11)

flag = 1
for i in range(3):
    if i:
        break
    log('a')
    raise SystemExit
if flag == 1:
    pass
elif flag == -1:
    log('b')
log('after')
