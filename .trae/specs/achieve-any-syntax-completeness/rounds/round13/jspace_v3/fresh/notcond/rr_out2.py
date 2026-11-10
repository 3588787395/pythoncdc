# Source Generated with Decompyle++ (Python version)
# File: rr.pyc (Python 3.11)

class Handler:
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Return a Request or None in response to a redirect."""
        m = req.get_method()
        if not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD') or code in (301, 302, 303) and m == 'POST'):
            raise ValueError(req.full_url, code, msg, headers, fp)
        newurl = newurl.replace(' ', '%20')
        CONTENT_HEADERS = ('content-length', 'content-type')
        newheaders = {k: v for k, v in req.headers.items() if k.lower() not in CONTENT_HEADERS}
        return Request(newurl, headers=newheaders, origin_req_host=req.origin_req_host, unverifiable=True)
