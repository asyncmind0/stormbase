import tornado.auth
from tornado import httpclient
from tornado import httputil
from tornado.httputil import url_concat
from tornado import escape
import logging
import urllib
import httplib

import gdata.gauth
import gdata.contacts.service
import gdata.contacts.client
import gdata.contacts.data


class GoogleOAuth2Mixin(tornado.auth.OAuth2Mixin):

    access_token = ""
    _OAUTH_AUTHENTICATE_URL = "https://accounts.google.com/o/oauth2/auth"
    _OAUTH_ACCESS_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    _OAUTH_TOKEN_VALIDATION_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    _USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    @property
    def httpclient_instance(self):
        return httpclient.AsyncHTTPClient()

    def authorize_redirect(self, scope, redirect_uri, **kwargs):
        args = {
            "redirect_uri": redirect_uri,
            "client_id": self.settings['google_consumer_key'],
            "response_type": "code",
            "scope": scope,
            "state": kwargs.get('state', '')
        }
        if kwargs:
            args.update(kwargs)
        url = url_concat(self._OAUTH_AUTHENTICATE_URL, args)
        print url
        self.redirect(url)

    def get_authenticated_user(self, authorization_code, callback,
                               redirect_uri):
        args = {
            "redirect_uri": redirect_uri,
            "client_id": self.settings['google_consumer_key'],
            "code": authorization_code,
            "client_secret": self.settings['google_consumer_secret'],
            "grant_type": "authorization_code"
        }

        body = urllib.urlencode(args)
        request = httpclient.HTTPRequest(self._OAUTH_ACCESS_TOKEN_URL,
                                         method="POST",
                                         body=body)

        self.httpclient_instance.fetch(
            request,
            self.async_callback(self._on_access_token, callback)
        )

    def _on_access_token(self, callback, response):
        if response.error:
            logging.warning('Google auth error: %s%s' %
                            (str(response), response.body))
            callback(None)
            return

        session = escape.json_decode(response.body)
        print 'session: ', session
        GoogleOAuth2Mixin.access_token = session['access_token']
        #callback(session)
        self.validate_token(session, callback)

    def validate_token(self, session, callback):
        self.httpclient_instance.fetch(
            self._OAUTH_TOKEN_VALIDATION_URL + "?access_token="
            + session['access_token'],
            self.async_callback(self.get_user_info, session, callback)
        )

    def get_contacts(self, session, callback, response):
        client = gdata.contacts.client.ContactsClient(source='pulp')
        client.auth_token = session['access_token']
        query = gdata.contacts.client.ContactsQuery()
        query.max_results = 999999999
        feed = client.GetContacts(q=query)
        for contact in feed.entry:
            contact_name = contact.name.full_name.text if contact.name else ''
            for email in contact.email:
                print 'Contact: %s, name: %s' % (email.address, contact_name)

    def get_user_info(self, session, callback, response):
        GoogleOAuth2Mixin.access_token = session['access_token']
        print GoogleOAuth2Mixin.access_token
        additional_headers = {
            "Authorization": "Bearer " + GoogleOAuth2Mixin.access_token
        }
        h = httputil.HTTPHeaders()
        h.parse_line("Authorization: Bearer " + GoogleOAuth2Mixin.access_token)
        conn = httplib.HTTPSConnection("www.googleapis.com")
        conn.request("GET",
                     "/oauth2/v1/userinfo?access_token="
                     + GoogleOAuth2Mixin.access_token,
                     "", additional_headers)
        response = conn.getresponse()
        #h.pop("Accept-Encoding")
        '''request = httpclient.HTTPRequest(self._USER_INFO_URL+"?access_token="+GoogleOAuth2Mixin.access_token, method="GET", headers=h)
        self.httpclient_instance.fetch(
            request,
            self.async_callback(callback)
        )'''
        self._on_response(response, callback)

    def _on_response(self, response, callback):
        if response.status != 200:
            logging.warning('Google get user info error: %s' % str(response))
            callback(None)
            return

        user_info = escape.json_decode(response.read())
        print 'user_info: ', user_info
        callback(user_info)
