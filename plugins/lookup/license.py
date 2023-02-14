#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: license
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: get license overview for Qlik Cloud tenant
  description:
      - This lookup returns the license overview for a Qlik Cloud tenant.
  options:
    _terms:
      description: not used
      required: False
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
  notes:
    - search term is not used.
"""


from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils.common.text.converters import to_native

from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Qlik


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        api_key = self.get_option('api_key')
        if api_key == None:
            api_key = self._templar.template(variables['access_token'])

        client = Qlik(Config(
            host='https://%s' % variables["inventory_hostname"],
            auth_type=AuthType.APIKey,
            api_key=api_key))

        ret = []
        try:
            license = client.licenses.get_overview()
            ret.append(license)
            return ret
        except HTTPError as err:
            raise AnsibleError('Error getting license, HTTP %s: %s' % (
                err.response.status_code, err.response.text))
        except Exception as err:
            raise AnsibleError('Error getting license: %s' % to_native(err))
