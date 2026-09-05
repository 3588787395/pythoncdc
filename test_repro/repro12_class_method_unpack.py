"""Repro 12: yield from with unpack in class method"""
class Handler:
    def run(self):
        yield self.setup()
        host, port = yield from self.connect()
        self.server.host = host
        self.server.port = port

code = Handler.run.__code__
import dis
dis.dis(code)
