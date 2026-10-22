class URL:
    def __init__(self, url):
        self.scheme = 'http'
        self.port = None
        self.target = url


def main():
    u = URL('/x')
    print(u.scheme, u.port, u.target)
