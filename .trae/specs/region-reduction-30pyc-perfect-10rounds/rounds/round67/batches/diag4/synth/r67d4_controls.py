class E(Exception):
    pass


def g():
    return 1


def c1_pass_true():
    while True:
        try:
            return g()
        except E:
            pass


def c2_pass_cond():
    while g():
        try:
            return g()
        except E:
            pass


def c3_cont_cond():
    while g():
        try:
            return g()
        except E:
            continue


def c4_cont_for():
    for i in g():
        try:
            g()
        except E:
            continue


def c5_cont_true_noreturn():
    while True:
        try:
            g()
        except E:
            continue
