def fetch(self, meth, url, headers):
    self.tries += 1
    try:
        if self.maxtries and self.tries >= self.maxtries:
            if hasattr(self, 'http_error_500'):
                meth = self.http_error_500
            else:
                meth = self.http_error_default
            return meth(url, self, 500, 'Internal Server Error: Redirect Recursion', headers)
        result = self.redirect_internal(url, self)
        return result
    finally:
        self.tries = 0
