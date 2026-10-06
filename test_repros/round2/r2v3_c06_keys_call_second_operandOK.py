# Source Generated with Decompyle++ (Python version)
# File: r2v3_c06_keys_call_second_operand.pyc (Python 3.11)

def f(username, uinfo, acct):
    n = 0
    if username not in uinfo.keys() or not uinfo[username]:
        acct.lock.acquire()
        try:
            for m in JOBS:
                n = n + 1
                if n is None:
                    return 2
            return 1
        except BaseException:
            acct.lock.release()
            acct.lock.release()
            return 2
        finally:
            acct.lock.release()
