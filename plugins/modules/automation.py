#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: automation
version_added: "0.1.0"
short_description: Manages automations in Qlik Cloud.
description:
    - Manages automations in Qlik Cloud.
options:
  id:
    description:
      - ID of the automation
    required: false
  name:
    description:
      - The name of the automation
    required: true
  description:
    description:
      - The description of the automation
    required: false
  workspace:
    description:
      - The description of the automation
    required: false
  state:
    description:
      - State of the automation
    required: false
    choices:
      - present
      - absent
      - triggered
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
  # Trigger an automation
  automation:
    name: My Automation
    state: triggered

  # Rename an automation
  automation:
    id: ef8d810f-13e2-4bdb-8c51-2309cba4ae5c
    name: My Automation

  # Create an automation
  automation:
    name: My Automation
    workspace: "{{ lookup('file', 'myautomation.json') }}"
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import Automations, RunDetailRequestObject


class QlikAutomationManager(QlikCloudManager):
    client: Automations

    def __init__(self, module: AnsibleModule):
        self.type = 'automation'
        self.results = {
            'changed': False,
            'automation': {},
        }
        self.resource = {}
        self.client = helper.get_client(module, Automations)
        self.states_map = {
            'present': self.ensure_present,
            'absent': self.ensure_absent,
            'triggered': self.trigger}

        super().__init__(module)

    def existing(self):
        '''Return existing reload task'''
        if self.resource != {}:
            return self.resource
        
        automation_id = self.module_params['id']

        if not automation_id:
            results = self.client.get_automations(filter=f'name eq "{self.module_params["name"]}"')
            if len(results) > 0:
                automation_id = results[0].id

        self.resource = self.client.get(automation_id)
        return self.resource

    def trigger(self):
        self.ensure_present()
        self.resource.create_run(RunDetailRequestObject(context='api'))


def main():
    module_args = dict(
        id=dict(type='str', required=False),
        name=dict(type='str', required=True),
        description=dict(type='str', required=False),
        workspace=dict(type='json', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikAutomationManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
