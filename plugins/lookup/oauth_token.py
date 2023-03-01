#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: oauth_token
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: get oauth token for Qlik Cloud tenant
  description:
      - This lookup returns an oauth access token for a Qlik Cloud tenant.
  options:
    client_id:
      description:
        - Client ID for the region of the tenant
      type: string
    client_secret:
      description:
        - Client secret associated with the ID
      type: string
    flat:
      description:
        - If set to I(True), the return value will be the access token only.
        - Otherwise the full OAuth token object will be returned.
      type: bool
      default: true
"""


from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from ..module_utils import oauth


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        display = Display()
        display.vvvvv('Running oauth lookup plugin')

        client_id = self.get_option('client_id')
        if client_id == None:
            client_id = self._templar.template(variables['client_id'])

        client_secret = self.get_option('client_secret')
        if client_secret == None:
            client_secret = self._templar.template(variables['client_secret'])

        token = oauth.get_access_token(
            hostname=variables["ansible_host"],
            client_id=client_id,
            client_secret=client_secret)

        if self.get_option('flat'):
            return [token['access_token']]
        else:
            return [token]
