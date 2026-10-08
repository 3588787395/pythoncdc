# Source Generated with Decompyle++ (Python version)
# File: r10g7_17_ctl_rotatingfilehandler_twin.pyc (Python 3.11)

def r10g7_17_ctl_rotatingfilehandler_twin(self, running, stream):
    while running:
        try:
            if self.buf.tell():
                stream = self.buf
                self.buf = io.StringIO()
            else:
                if self.waiting_to_end or self._check_main():
                    self.running = False
                time.sleep(self.timeout)
            stream.seek(0)
            text = stream.read()
        except (IOError, EOFError, ValueError):
            if self.waiting_to_end or self._check_main():
                self.running = False
        if text:
            return text
    return None
