class C62:
    def __init__(self):
        self.running = 1

    def _target(self):
        while self.running:
            print('tick')
