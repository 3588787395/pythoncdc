# Source Generated with Decompyle++ (Python version)
# File: r4v3_b07_positive_polarity.pyc (Python 3.11)

class M:
    def reload(self):
        if self.pre_flag and self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
