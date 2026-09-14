
def load(self):
    try:
        with open('test', 'r') as f:
            data = f.read()
            result = None
            return result
    except Exception:
        return None
