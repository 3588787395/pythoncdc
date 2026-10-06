# Source Generated with Decompyle++ (Python version)
# File: r2v3_c09_method_host_or_not_operand.pyc (Python 3.11)

class C:
    def m(self, username, uinfo):
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
        return 1
