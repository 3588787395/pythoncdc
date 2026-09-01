# repro_01: SWAP(2)+POP_TOP+RETURN_VALUE in for loop (expr_stmt + return None)
# Pattern from np_tp_pd: for loop body with expr statement followed by return None
# CPython optimizes to: CALL + SWAP(2) + POP_TOP + RETURN_VALUE
def f(items):
    for item in items:
        process(item)
        return None
