"""c14: class docstring and non-docstring first statements."""
class CDoc:
    """Class docstring."""
    A = 1

    def m(self):
        """Method docstring."""
        return self.A


class CNoDoc:
    A = 0
    """Not a docstring (constant expr after assign)."""

    def m(self):
        return self.A


class CDocDeep:
    """Doc plus deep body."""
    if 1:
        for i in range(1):
            while i:
                try:
                    i -= 1
                finally:
                    pass
        B = [i]

    def n(self):
        return B
