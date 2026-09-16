import dis

def p4():
    if not a or not b:
        then_body()

dis.dis(p4)

print()

def p5():
    if not a and not b:
        then_body()

dis.dis(p5)

print()

# What about the original pattern: guard clause with early return
def p6():
    if not a or b:
        early_return()
    else:
        main_body()

dis.dis(p6)
