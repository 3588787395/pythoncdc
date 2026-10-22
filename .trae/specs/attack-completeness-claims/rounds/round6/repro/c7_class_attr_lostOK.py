# Source Generated with Decompyle++ (Python version)
# File: c7_class_attr_lost.pyc (Python 3.11)

class URL:
    def __init__(self, url):
        self.scheme = 'http'
        self.port = None
        self.target = url
def main():
    u = URL('/x')
    print(u.scheme, u.port, u.target)
