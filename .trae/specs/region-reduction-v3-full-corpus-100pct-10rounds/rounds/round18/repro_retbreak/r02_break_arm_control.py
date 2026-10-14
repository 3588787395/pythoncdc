
import time
def f(self):
    while True:
        while not self.stop:
            if self.flag:
                break
            time.sleep(0.01)
        else:
            return None
        if self.stop:
            return None
