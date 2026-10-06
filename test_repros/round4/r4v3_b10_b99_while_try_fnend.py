class TWH:
    def _target(self):
        while self.running:
            try:
                self.tick()
            except Exception:
                LOG.error('boom')
            else:
                self.ok += 1
