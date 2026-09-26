# Source Generated with Decompyle++ (Python version)
# File: b08_not_in_membership_guard.pyc (Python 3.11)

def check_industry_code(self, s, industry_codes):
    if not ('%s.csv' % s[:-5] in industry_codes or '%s.csv' % s[:-3] in industry_codes):
        self.trade_log.error('您输入的指数代码有误')
    if '%s.csv' % s[:-5] not in industry_codes:
        assert '%s.csv' % s[:-3] in industry_codes, '您输入的指数代码有误'
        return None
    else:
        return None
