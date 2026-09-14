
def load(self):
    try:
        with open('test', 'r') as future_file:
            _future_info = future_file.read()
            self.future_info = eval(_future_info)
            return None
    except Exception:
        return None
