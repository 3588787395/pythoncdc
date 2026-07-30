# Pattern: class __init__ with instance attribute assignments
# Function: BasicDataSource.__init__
# Expected: self.a = x; self._b = True; self._c = obj(path)
# Actual: same (pyc 100% match, NO-DEFECT control)
import os
class BasicDataSource(object):
    def __init__(self, data_path=''):
        self.data_path = data_path
        self._inited = True
        self._exrights = os.path.join(data_path, 'exrights.pk')
# NO-DEFECT
