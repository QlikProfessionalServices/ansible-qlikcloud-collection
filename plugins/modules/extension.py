#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: extension
version_added: "0.1.0"
short_description: Manages extensions in Qlik Cloud.
description:
    - Manages extensions in Qlik Cloud.
options:
  name:
    description:
      - Name of the extension
    required: true
  file:
    description:
      - Path to an extension archive
    required: true
  type:
    description:
      - The type of this extension (visualization, etc.).
    choices:
      - visualization
    default: visualization
  state:
    description:
      - State of the extension
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
  # Import extension
  extension:
    name: my_extension
    file: files/my_extension.zip
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import Extensions


class QlikExtensionManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'extension'
        self.results = {
            'changed': False,
            'extension': {},
        }
        self.resource = {}
        self.client = helper.get_client(module, Extensions)

        super().__init__(module)

    def existing(self):
        '''Return existing extension'''
        if self.resource != {}:
            return self.resource

        results = self.client.get_extensions()
        for ext in results.data:
            if ext.name == self.module_params['name']:
                self.resource = ext
                return ext

        return self.resource

    def create(self):
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
        type=dict(type='str', required=False, default='visualization', options=['visualization']),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikExtensionManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
