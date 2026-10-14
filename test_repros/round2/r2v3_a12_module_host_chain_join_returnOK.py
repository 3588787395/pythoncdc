# Source Generated with Decompyle++ (Python version)
# File: r2v3_a12_module_host_chain_join_return.pyc (Python 3.11)

flag = poll()
redata = get()
if flag == 1:
    log('a')
elif flag == -1:
    log('b')
return_if_true(redata)
log('after')
