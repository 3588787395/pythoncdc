
def load(self):
    try:
        with open('test', 'r') as f:
            data = f.read()
            return None
    except Exception:
        return None
