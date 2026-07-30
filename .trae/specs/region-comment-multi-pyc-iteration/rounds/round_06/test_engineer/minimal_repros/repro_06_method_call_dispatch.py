# Pattern: method dispatching to another method (get_security_info -> get_security_info_lru)
# Function: BasicDataSource.get_security_info else branch
# Expected: else: return self.other_method(x)
# Actual: same (pyc 100% match, NO-DEFECT control)
class DataSource(object):
    def get_info(self, symbols=None):
        if isinstance(symbols, list):
            return symbols
        else:
            return self.get_info_lru(symbols)
    def get_info_lru(self, symbols=None):
        return symbols
# NO-DEFECT
