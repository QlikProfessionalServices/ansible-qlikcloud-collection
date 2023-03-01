#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: group
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: lookup groups in a Qlik Cloud tenant
  description:
      - This lookup returns the details of groups from a Qlik Cloud tenant.
  options:
    _terms:
      description: filter to use for the query
      required: True
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
    flat:
      description:
        - If set to I(True), the return value will be the group ID only.
        - Otherwise the full group object will be returned.
      type: bool
      default: true
  notes:
    - if read in variable context, the file can be interpreted as YAML if the content is valid to the parser.
    - this lookup does not understand globbing --- use the fileglob lookup instead.
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

        api_key = self.get_option('api_key')
        if api_key == None:
            api_key = self._templar.template(variables['access_token'])

        client = Qlik(Config(
            host='https://%s' % variables["ansible_host"],
            auth_type=AuthType.APIKey,
            api_key=api_key))

        display = Display()
        ret = []
        for term in terms:
            display.debug("Group lookup term: %s" % term)
            filter = '(name eq "%s")'
            query = Filter(filter=filter % term)
            display.vvvv(u"Group lookup using filter '%s'" % query.filter)
            try:
                groups = client.groups.filter(query)

                if groups:
                    ret.extend([asdict(group) for group in groups])
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("No results from group lookup: %s" % term)
            except HTTPError as err:
                AnsibleError('Error in user lookup, HTTP %s: %s' % (
                        err.response.status_code, err.response.text))

        if self.get_option('flat'):
            ret = [group['id'] for group in ret]
        return ret
