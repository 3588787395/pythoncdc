"""AT-02/B142: for x try/finally x try/finally —— 两级 finally 副本 + continue"""


def a3(xs):
    for x in xs:
        try:
            try:
                if x:
                    continue
                else:
                    break
            finally:
                print('inner-fin')
        finally:
            print('outer-fin')
