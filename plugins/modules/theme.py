#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: theme
version_added: "0.1.0"
short_description: Manages themes in Qlik Cloud.
description:
    - Manages themes in Qlik Cloud.
options:
  name:
    description:
      - Name of the theme
    required: true
  file:
    description:
      - Path to the theme file
    required: true
  type:
    description:
      - The type of this theme (visualization, etc.).
    choices:
      - theme
    default: theme
  state:
    description:
      - State of the theme
    required: false
    choices:
      - present
      - absent
    default: present
  tenant_uri:
    description:
      - Base URI of the tenant
    required: true
  api_key:
    description:
      - Bearer token for authentication
    required: true
'''

EXAMPLES = '''
  # Import theme
  theme:
    name: My Theme
    file: files/my_theme.zip
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import Themes


class QlikThemeManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'theme'
        self.results = {
            'changed': False,
            'theme': {},
        }
        self.resource = {}
        self.client = helper.get_client(module, Themes)

        super().__init__(module)

    def existing(self):
        '''Return existing theme'''
        if self.resource != {}:
            return self.resource

        results = self.client.get_themes()
        for ext in results:
            if ext.name == self.module_params['name']:
                self.resource = ext
                return ext

        return self.resource

    def create(self):
        '''Upload a theme'''
        if self.module.check_mode:
            return self.existing()

        try:
            with open(self.module_params['file'], 'rb') as f:
                new_resource = self.client.create(file=f, data=self.desired)
                return new_resource
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results)


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        file=dict(type='str', required=True),
        type=dict(type='str', required=False, default='theme', options=['theme']),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikThemeManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
