class M:
    def reload(self):
        if self.pre_flag:
            if self.upd_flag:
                self._dates = self.engine.cal.get()
                self.upd_flag = True
