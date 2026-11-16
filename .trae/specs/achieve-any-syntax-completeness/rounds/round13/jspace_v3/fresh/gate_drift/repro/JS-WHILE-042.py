def g4b_wt_with_continue(p, a):
    while True:
        with open(p) as f:
            if a:
                continue
            return 4
if __name__ == '__main__':
    print(g4b_wt_with_continue(__file__, 0))
