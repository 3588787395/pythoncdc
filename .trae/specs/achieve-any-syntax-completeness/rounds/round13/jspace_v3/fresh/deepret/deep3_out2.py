# Source Generated with Decompyle++ (Python version)
# File: deep3.pyc (Python 3.11)

def f(domains, authuri, cond):
    for default_port in (True, False):
        reduced = cond(authuri, default_port)
        for uris, authinfo in domains.items():
            for uri in uris:
                if self_check(uri, reduced):
                    return authinfo
    return (None, None)
