# Source Generated with Decompyle++ (Python version)
# File: r4v3_b04_single_if_control.pyc (Python 3.11)

class M:
    def reload(self):
        if not self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
            return None
        else:
            return None
