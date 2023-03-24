#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: app_object
  author: Adam Haydon
  version_added: "0.1.0"  # for collections, use the collection version, not the Ansible version
  short_description: lookup objects in a Qlik Sense app
  description:
      - This lookup returns the objects in a Qlik Sense app.
  options:
    _terms:
      description:
        - Types of the objects to lookup.
      required: True
    app_id:
      description:
        - The ID of the app to lookup objects.
      type: string
      required: True
    api_key:
      description:
        - OAuth token to authenticate to the tenant
      type: string
    flat:
      description:
        - If set to I(True), the return value will be the object ID only.
        - Otherwise the properties of the object will be returned.
      type: bool
      default: True
  notes:
    - an empty search term will return all objects in the app.
"""

from typing import *

from ansible.errors import AnsibleError, to_native
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from dataclasses import asdict
from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Qlik, NxGetObjectOptions, NxContainerEntry


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        display = Display()

        self.set_options(var_options=variables, direct=kwargs)

        api_key = self.get_option('api_key')
        if api_key == None:
            api_key = self._templar.template(variables['access_token'])

        client = Qlik(Config(
            host='https://%s' % variables["ansible_host"],
            auth_type=AuthType.APIKey,
            api_key=api_key))

        try:
            display.v('Opening app')
            app = client.apps.get(self.get_option('app_id'))
        except HTTPError as err:
            raise AnsibleError('Error getting app, HTTP %s: %s' % (
                err.response.status_code, err.response.text))

        ret = []
        try:
            with app.open():
                ret: List[NxContainerEntry] = app.get_objects(NxGetObjectOptions(qTypes=terms))
                display.v('Object count: %s' % len(ret))
        except Exception as err:
            raise AnsibleError('Error opening app: %s' % (to_native(err)))

        if self.get_option('flat'):
            ret = [obj.qInfo.qId for obj in ret]
        else:
            ret = [asdict(obj) for obj in ret]
        return ret
