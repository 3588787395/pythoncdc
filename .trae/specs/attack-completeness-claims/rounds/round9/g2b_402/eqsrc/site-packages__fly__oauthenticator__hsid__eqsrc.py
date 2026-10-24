# Source Generated with Decompyle++ (Python version)
# File: hsid.pyc (Python 3.11)

import json
import os
import urllib
from tornado import gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from .oauth2 import OAuthLoginHandler, OAuthenticator
from tornado.log import app_log
from IQCommon.common import LOGIN_URL
TOKEN_FILE = './jupyterhub_tokens'
PWDKEY = 25
class HSIDOAuthenticator(OAuthenticator):
    fly_sys_version = 'sns'
    login_service = 'HSID'
    login_handler = OAuthLoginHandler
    hsid_login_url = LOGIN_URL
    if hsid_login_url is '':
        pass
    @gen.coroutine
    def authenticate(self, handler):
        userId = handler.get_argument('username', False)
        pwd = handler.get_argument('password', False)
        if not userId:
            return (None, '请输入用户名')
        elif not pwd:
            return (None, '请输入密码')
        else:
            http_client = AsyncHTTPClient()
            body = urllib.parse.urlencode({'auth_username': userId, 'auth_password': pwd})
            req = HTTPRequest(f'{self.hsid_login_url!s}?{body!s}', method='GET', headers={'Content-Type': 'application/x-www-form-urlencoded'})
            resp = yield http_client.fetch(req)
            resp_json = json.loads(resp.body.decode('utf8', 'replace'))
            if 'error_info' in resp_json:
                return (None, resp_json['error_info'])
            else:
                username = resp_json['data'][0]['auth_id']
                user_token = resp_json['data'][0]['user_token']
                if self.whitelist and username not in self.whitelist:
                    username = None
                if username:
                    self.saveToken(username, user_token)
                return (username, '')
    def saveToken(self, username, token):
        tokens = {}
        if os.path.exists(TOKEN_FILE):
            f = open(TOKEN_FILE, 'r+')
            tokens = json.load(f)
            f.close()
        tokens[username] = token
        f = open(TOKEN_FILE, 'w')
        json.dump(tokens, f)
        f.close()
