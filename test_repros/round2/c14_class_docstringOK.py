# Source Generated with Decompyle++ (Python version)
# File: c14_class_docstring.pyc (Python 3.11)

__doc__ = 'c14: class docstring and non-docstring first statements.'
class CDoc:
    __doc__ = 'Class docstring.'
    A = 1
    def m(self):
        """Method docstring."""
        return self.A
class CNoDoc:
    A = 0
    """"""
    def m(self):
        return self.A
class CDocDeep:
    __doc__ = 'Doc plus deep body.'
    for i in range(1):
        while i:
            try:
                i -= 1
            finally:
                pass
    B = [i]
    def n(self):
        return B
