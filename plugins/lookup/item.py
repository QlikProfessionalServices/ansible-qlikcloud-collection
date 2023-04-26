#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: item
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: lookup items in a Qlik Cloud tenant
  description:
      - This lookup returns the details of items from a Qlik Cloud tenant.
  options:
    resource_type:
      description:
        - The type of the resource to lookup.
    resource_id:
      description:
        - The ID of the resource to lookup.
    space:
      description:
        - The name of the space to lookup items.
    owner_id:
      description:
        - The ID of the owner of the items.
    tenant:
      description:
        - Hostname of the Qlik Cloud tenant
      type: string
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
    flat:
      description:
        - If set to I(True), the return value will be the item ID only.
        - Otherwise the full item properties will be returned.
      type: bool
      default: true
"""


from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from requests.exceptions import HTTPError
from dataclasses import asdict

from qlik_sdk import AuthType, Config, Qlik

display = Display()


class LookupModule(LookupBase):

    def get_items(self, query):
        try:
            items = self.client.items.get_items(**query)
            return [item for item in items.pagination] if items else []
        except AnsibleParserError:
            raise AnsibleError("No results from item lookup: %s" % query)
        except HTTPError as err:
            raise AnsibleError('Error in item lookup, HTTP %s: %s' % (
                err.response.status_code, err.response.text))

    def run(self, terms, variables=None, **kwargs):
      display.v('Lookup items')

      self.set_options(var_options=variables, direct=kwargs)

      api_key = self.get_option('api_key')
      if api_key == None:
          api_key = self._templar.template(variables['access_token'])

      host = self.get_option('tenant')
      if not host:
          host = variables["ansible_host"]

      self.client = Qlik(Config(
          host=f'https://{host}',
          auth_type=AuthType.APIKey,
          api_key=api_key))

      space_name = self.get_option('space')
      if space_name:
          space_id = self.client.spaces.get_spaces(filter=f'name eq "{space_name}"')
      else:
          space_id = space_name

      query = {
          'resourceType': self.get_option('resource_type'),
          'resourceId': self.get_option('resource_id'),
          'spaceId': space_id,
          'ownerId': self.get_option('owner_id'),
      }
      display.v(f'query: {query}')
      if not query:
          query = {}

      ret = self.get_items(query) if not terms else []

      if self.get_option('flat'):
          ret = [item.id for item in ret]
      else:
          ret = [asdict(item) for item in ret]

      display.v(f'return: {ret}')
      return ret
