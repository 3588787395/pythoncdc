import dis

def p3():
    if not (a and not b):
        then_body()
    else:
        else_body()

dis.dis(p3)
