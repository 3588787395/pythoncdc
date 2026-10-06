# Source Generated with Decompyle++ (Python version)
# File: r4v3_b08_three_nested.pyc (Python 3.11)

class M:
    def reload(self):
        if not (self.a_flag and self.b_flag and self.c_flag):
            self._dates = self.engine.cal.get()
            self.upd_flag = True
            return None
