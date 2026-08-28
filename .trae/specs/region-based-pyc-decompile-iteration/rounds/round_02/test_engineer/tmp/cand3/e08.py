class A:
    def __init__(self, p=None):
        self.x = 1
        self.y = p if p is not None else []
        self.z = 0
