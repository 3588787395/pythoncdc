# Source Generated with Decompyle++ (Python version)
# File: r4v3_b10_b99_while_try_fnend.pyc (Python 3.11)

class TWH:
    def _target(self):
        while self.running:
            try:
                self.tick()
            except Exception:
                LOG.error('boom')
            else:
                self.ok += 1
