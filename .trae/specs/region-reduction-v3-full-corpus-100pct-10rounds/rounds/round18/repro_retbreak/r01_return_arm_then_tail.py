
import time
def f(self):
    while True:
        while not self.stop:
            if self.flag:
                return None
            time.sleep(0.01)
            if self.stop:
                return None
        else:
            return None
