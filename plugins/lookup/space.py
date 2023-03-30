#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: space
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: lookup spaces in a Qlik Cloud tenant
  description:
      - This lookup returns the details of spaces from a Qlik Cloud tenant.
  options:
    _terms:
      description: Name of the space to lookup
      required: False
    filter:
      description:
        - The advanced filtering to use for the query.
        - Use %s in the filter as a placeholder for the search term.
      type: string
      default: (name eq "%s")
      ini:
        - section: qlik_space_lookup
          key: filter
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
    flat:
      description:
        - If set to I(True), the return value will be the user ID only.
        - Otherwise the full user object will be returned.
      type: bool
      default: true
  notes:
    - an empty search term will lookup the user associated with the api key.
"""


from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Qlik, Filter

display = Display()


class LookupModule(LookupBase):

    def get_spaces(self, filter):
        try:
            if (filter):
                query = Filter(filter=filter)
                display.vvv(u"Space lookup using filter '%s'" % query.filter)
                spaces = self.client.spaces.filter(query)
            else:
                spaces = self.client.spaces.get_spaces()

            if spaces:
                return [space for space in spaces.pagination]
            else:
                raise AnsibleParserError()
        except AnsibleParserError:
            raise AnsibleError("No results from space lookup: %s" % filter)
        except HTTPError as err:
            AnsibleError('Error in space lookup, HTTP %s: %s' % (
                err.response.status_code, err.response.text))

    def run(self, terms, variables=None, **kwargs):
      display.v('Lookup spaces')

      self.set_options(var_options=variables, direct=kwargs)

      api_key = self.get_option('api_key')
      if api_key == None:
          api_key = self._templar.template(variables['access_token'])

      self.client = Qlik(Config(
          host='https://%s' % variables["ansible_host"],
          auth_type=AuthType.APIKey,
          api_key=api_key))

      self.filter = self.get_option('filter')
      if not self.filter:
          self.filter = '(name eq "%s")'

      ret = self.get_spaces('') if not terms else []
      for term in terms:
          ret.extend(self.get_spaces(self.filter % term))

      if self.get_option('flat'):
          ret = [space.id for space in ret]
      return ret
