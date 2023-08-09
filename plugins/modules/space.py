#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: space
version_added: "0.1.0"
short_description: Manages spaces in Qlik Cloud.
description:
    - Manages spaces in Qlik Cloud.
options:
  name:
    description:
      - Name of the space
    required: true
  type:
    description:
      - Type of space
    required: true
    choices:
      - data
      - managed
      - shared
    default: shared
  description:
    description: The description of the space
    required: false
  owner_id:
    description: The user ID in uid format (string) of the space owner
    required: false
  state:
    description:
      - State of the space
    required: false
    choices:
      - present
      - absent
    default: present
  allow_recreate:
    description: Allow space to be deleted and recreated if the type changes
    default: false
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
  # Create a new shared space.
  space:
    name: Test
    type: shared

  # Create a new managed space.
  space:
    name: Published Apps
    type: managed

  # Create a new data space.
  space:
    name: Data Files
    type: data

  # Change the owner of an existing space.
  space:
    name: Test
    owner_id: R2aCCzAa_fvf1s-NI9XU2y467l-g4sX6
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import Spaces


class QlikSpaceManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'space'
        self.results = {
            'changed': False,
            'space': {},
        }
        self.resource = {}
        self.desired = helper.construct_state_from_params(
            module.params, ignore_params=['allow_recreate'])
        self.patchable = ['name', 'description', 'ownerId']
        self.client = helper.get_client(module, Spaces)

        super().__init__(module)

    def existing(self):
        '''Return existing space'''
        if self.resource != {}:
            return self.resource

        results = self.client.get_spaces(name=self.module_params["name"],limit=100)
        if len(results) > 0:
            self.resource = results[0]
        return self.resource

    def update(self):
        if not self.module_params['allow_recreate']:
            self.module.warn('Space type changed but allow_recreate set to false')
            return

        self.delete()
        return self.create()


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        type=dict(type='str', required=True),
        description=dict(type='str', required=False),
        owner_id=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present'),
        allow_recreate=dict(type='bool', required=False, default=False),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikSpaceManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
