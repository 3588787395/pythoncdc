# Source Generated with Decompyle++ (Python version)
# File: r1_35_cand_method_try_nest.pyc (Python 3.11)

class K:
    def m(self, x):
        try:
            if x == 1:
                if x == 2:
                    print('a')
                else:
                    print('b')
                print('c')
                return None
            else:
                print('d')
                return None
        except BaseException as exc:
            print(exc)
            return None
