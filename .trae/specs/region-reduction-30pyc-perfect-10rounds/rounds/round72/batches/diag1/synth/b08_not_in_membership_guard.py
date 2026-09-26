# F-OTHER (quote.check_industry_code): `if not X in Y:` guards.  The original
# compiles the membership test as CONTAINS_OP `in` followed by a conditional
# jump; the decompiler rewrites the guard as `if X not in Y:` so the product
# carries CONTAINS_OP `not in` (+ inverted jump) at the same index -> first
# divergent instruction CONTAINS_OP in -> CONTAINS_OP not in.
def check_industry_code(self, s, industry_codes):
    if not ('%s.csv' % s[:-5] in industry_codes or '%s.csv' % s[:-3] in industry_codes):
        self.trade_log.error('您输入的指数代码有误')
    if not '%s.csv' % s[:-5] in industry_codes:
        assert '%s.csv' % s[:-3] in industry_codes, '您输入的指数代码有误'
        return None
