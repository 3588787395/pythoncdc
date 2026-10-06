# Source Generated with Decompyle++ (Python version)
# File: c4_06_try_finally_only.pyc (Python 3.11)

def e01_root(x):
    try:
        r = x + 1
        r = r if r else 0
        return r
    finally:
        r = r if r else 0
def e02_shallow(x):
    try:
        r = x
    finally:
        log(r)
    return r
def e03_deep(x):
    for i in range(3):
        if i:
            try:
                r = x + i
            finally:
                log(r)
            continue
    return r
def e04_nested(x):
    try:
        try:
            r = x
        finally:
            a = 1
    finally:
        b = 2
    return r
def e05_with(x):
    with open('a') as f:
        try:
            r = f.read()
        finally:
            f.close()
    return r
def e06_while(x):
    n = 0
    while n < 3:
        try:
            r = x + n
        finally:
            pass
        n += 1
    return r
class CF:
    def m(self, x):
        try:
            self.v = x
        finally:
            self.v = 0
        return self.v
def e07_match_host(x):
    match x:
        case 0:
            try:
                r = 1
            finally:
                r = 2
        case _:
            r = 0
    return r
def e08_closure(x):
    def inner():
        try:
            return x
        finally:
            log(x)
    return inner()
def e09_comp_host(xs):
    return [x for x in xs if x]
