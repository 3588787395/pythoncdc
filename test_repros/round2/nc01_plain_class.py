"""nc01: plain class negative control."""
class KPlain:
    def a(self):
        return 1

    def b(self, v):
        if v:
            for i in range(v):
                while i:
                    i -= 1
        return v
