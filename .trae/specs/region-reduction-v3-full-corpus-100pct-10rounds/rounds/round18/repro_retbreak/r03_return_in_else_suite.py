
import time
def f(self):
    while not self.stop:
        try:
            v = self.q.get()
        except Empty:
            continue
        else:
            if v:
                return None
        time.sleep(0.01)
