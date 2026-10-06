# Source Generated with Decompyle++ (Python version)
# File: r3_b06_mixedjump_method_host.pyc (Python 3.11)

class C:
    def m(self, fq, div, fields):
        if fq is not None and div:
            if isinstance(fields, str) and 'x' in fields:
                need = 0
            else:
                need = 1
        for t in TYPES:
            use(need, t)
        return need
