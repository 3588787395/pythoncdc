
import time
def f(self):
    while not self.stop:
        if self.a:
            return None
        if self.b:
            return 1
        time.sleep(0.01)
