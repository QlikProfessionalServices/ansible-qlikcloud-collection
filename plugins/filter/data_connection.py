# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
  name: urlsplit
  version_added: "0.1"
  short_description: get components from connection string
  description:
    - Split a connection string into its component parts.
  positional: _input, query
  options:
    _input:
      description: Connection string for Qlik Sense data connection.
      type: str
      required: true
    query:
      description: Specify a single component to return.
      type: str
      required: false
'''

EXAMPLES = r'''

    connection_properties: '{{
        "CUSTOM CONNECT TO \"url=https://tenant.eu.qlikcloud.com/api/v2/items/;timeout=30\""
        | connstring_to_prop }}'
    # =>
    #   {
    #       "url": "https://tenant.eu.qlikcloud.com/api/v2/items/",
    #       "timeout": 30,
    #   }

    connection_properties: '{{
        "CUSTOM CONNECT TO \"url=https://tenant.eu.qlikcloud.com/api/v2/items/;timeout=30\""
        | connstring_to_prop("url") }}'
    # => 'https://tenant.eu.qlikcloud.com/api/v2/items/'

'''

RETURN = r'''
  _value:
    description:
      - A dictionary with components as keyword and their value.
      - If I(query) is provided, a string or integer will be returned instead, depending on I(query).
    type: any
'''

from ansible.errors import AnsibleFilterError


def connection_string_to_properties(value: str, query: str = ''):

    params = value.split('"')[1]

    try:
        results = {p[0]:p[1] for p in [i.split('=') for i in params.split(';') if i]}
    except:
        raise AnsibleFilterError('connstring_to_prop: invalid connection string: %s' % params)

    if query:
        if query not in results:
            raise AnsibleFilterError('connstring_to_prop: unknown property component: %s' % query)
        return results[query]
    else:
        return results

class FilterModule(object):
    ''' Ansible Qlik Cloud jinja2 filters '''

    def filters(self):
        return {
            'connstring_to_prop': connection_string_to_properties,
        }
