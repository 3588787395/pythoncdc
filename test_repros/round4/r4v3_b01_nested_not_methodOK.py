# Source Generated with Decompyle++ (Python version)
# File: r4v3_b01_nested_not_method.pyc (Python 3.11)

class M:
    def reload(self):
        if self.pre_flag:
            if not self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
                return None
