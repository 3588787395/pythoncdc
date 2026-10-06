# Source Generated with Decompyle++ (Python version)
# File: r4v3_b09_b99_while_try_ifarm.pyc (Python 3.11)

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
            return None
        else:
            return None
