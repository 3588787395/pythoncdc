# round-2 r2v3 specimen (synthetic, minimal)
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
            return 2
        finally:
            acct.lock.release()
    else:
        return 0
