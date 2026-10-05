# Source Generated with Decompyle++ (Python version)
# File: r1_65_cand_while_try_sinkpair.pyc (Python 3.11)

class C65:
    def __init__(self):
        self.running = 1
    def _target(self, v):
        if v == 3:
            while self.running:
                try:
                    print('get')
                except ValueError:
                    print('empty')
                else:
                    print('ok')
            return None
        elif v == 5:
            print('five')
        return None
