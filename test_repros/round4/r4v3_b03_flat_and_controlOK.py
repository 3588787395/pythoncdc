# Source Generated with Decompyle++ (Python version)
# File: r4v3_b03_flat_and_control.pyc (Python 3.11)

class M:
    def reload(self):
        if self.pre_flag:
            if not self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
                return None
