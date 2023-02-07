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
    _terms:
      description: not used
      required: False
    client_id:
      description:
        - Client ID for the region of the tenant
      type: string
    client_secret:
      description:
        - Client secret associated with the ID
      type: string
  notes:
    - search term is not used.
"""


from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils.common.text.converters import to_native

from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Auth


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        client = Auth(Config(
            host='https://%s' % variables["inventory_hostname"],
            auth_type=AuthType.OAuth2,
            scope=["user_default"],
            client_id=self.get_option('client_id'),
            client_secret=self.get_option('client_secret')))

        ret = []
        try:
            token = client.authorize()
            ret.append(token)
            return ret
        except HTTPError as err:
            raise AnsibleError('Error getting oauth token, HTTP %s: %s' % (
                err.response.status_code, err.response.text))
        except Exception as err:
            raise AnsibleError('Error getting oauth token: %s' % to_native(err))
