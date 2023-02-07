#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: user
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: lookup users in a Qlik Cloud tenant
  description:
      - This lookup returns the details of users from a Qlik Cloud tenant.
  options:
    _terms:
      description: filter to use for the query
      required: True
    filter:
      description:
        - The advanced filtering to use for the query.
        - Use %s in the filter as a placeholder for the search term.
      type: string
      default: (email eq "%s")
      ini:
        - section: qlik_user_lookup
          key: filter
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
  notes:
    - an empty search term will lookup the user associated with the api key.
"""


from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from dataclasses import asdict
from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Qlik, Filter


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

      self.set_options(var_options=variables, direct=kwargs)

      client = Qlik(Config(
          host='https://%s' % variables["inventory_hostname"],
          auth_type=AuthType.APIKey,
          api_key=self.get_option('api_key')))

      display = Display()

      if len(terms) == 0:
          display.vvvv("Lookup current user")
          try:
              return [client.users.get_me()]
          except HTTPError as err:
              AnsibleError('Error looking up current user, HTTP %s: %s' % (
                  err.response.status_code, err.response.text))

      filter = self.get_option('filter')
      if not filter:
          filter = '(email eq "%s")'

      ret = []
      for term in terms:
          display.debug("User lookup term: %s" % term)
          query = Filter(filter=filter % term)
          display.vvvv(u"User lookup using filter '%s'" % query.filter)
          try:
              users = client.users.filter(query)

              if users:
                  ret.extend([asdict(user) for user in users])
              else:
                  raise AnsibleParserError()
          except AnsibleParserError:
              raise AnsibleError("No results from user lookup: %s" % term)
          except HTTPError as err:
              AnsibleError('Error in user lookup, HTTP %s: %s' % (
                  err.response.status_code, err.response.text))

      return ret