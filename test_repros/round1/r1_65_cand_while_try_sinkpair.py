class C65:
    def __init__(self):
        self.running = 1

    def _target(self, v):
        if v == 3:
            while self.running:
                try:
                    print('get')
                except ValueError:
                    print('empty')
                else:
                    print('ok')
            return None
        if v == 5:
            print('five')
        return None
