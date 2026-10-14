# Source Generated with Decompyle++ (Python version)
# File: r4v3_b02_nested_not_sibling.pyc (Python 3.11)

class M:
    def reload(self):
        if self.pre_flag and not self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
        self.hit_count += 1
