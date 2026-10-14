class TWH:
    def _target(self):
        if self.sys_ver > 3:
            while self.running:
                try:
                    self.tick()
                except Exception:
                    LOG.error('boom')
                else:
                    self.ok += 1
