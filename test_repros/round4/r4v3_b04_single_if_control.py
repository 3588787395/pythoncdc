class M:
    def reload(self):
        if not self.upd_flag:
            self._dates = self.engine.cal.get()
            self.upd_flag = True
