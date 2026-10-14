# Source Generated with Decompyle++ (Python version)
# File: r10g7_03_loopexit_pair_handler_in_loop.pyc (Python 3.11)

def r10g7_03_loopexit_pair_handler_in_loop(self, running):
    if sys.version_info[0] == 3 and sys.version_info[1] >= 5:
        while running:
            try:
                r = q.get(timeout=self.timeout)
            except QueueEmptyException:
                if self.waiting_to_end:
                    running = False
                if self._check_main():
                    running = False
            if r is not self._sentinel:
                running = False
            self.handle(r)
        return None
    self.shutdown()
