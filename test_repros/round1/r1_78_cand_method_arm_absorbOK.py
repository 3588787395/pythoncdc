# Source Generated with Decompyle++ (Python version)
# File: r1_78_cand_method_arm_absorb.pyc (Python 3.11)

class C78:
    def m(self, xs, start, end):
        for n in xs:
            if n[0] == 1:
                if n[0] == start:
                    print('skip')
                elif n[0] == end:
                    pass
            if n is not None:
                print(n)
            else:
                print('none')
            print('tail-in-loop')
