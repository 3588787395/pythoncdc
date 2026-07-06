def test_c05_multiple_elif_chain():
    if cond1:
        do_1()
    elif cond2:
        do_2()
    elif cond3:
        do_3()
    elif cond4:
        do_4()
    else:
        do_default()
