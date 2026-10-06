class M:
    def reload(self):
        if self.a_flag:
            if self.b_flag:
                if not self.c_flag:
                    self._dates = self.engine.cal.get()
                    self.upd_flag = True
