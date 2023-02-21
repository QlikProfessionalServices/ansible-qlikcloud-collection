#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: app_object
version_added: "0.1.0"
short_description: Manages objects in Qlik Cloud apps.
description:
    - Manages objects in Qlik Cloud apps.
options:
  app_id:
    description:
      - ID of the app
    required: true
  id:
    description:
      - ID of the object
    required: true
  type:
    description:
      - type of the object
    required: true
  state:
    description:
      - State of the space
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
  # Create app object
  app_object:
    app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    id: EpsDdJ
    type: my-custom-hypercube
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import Apps, GenericObjectProperties, NxInfo


class QlikAppObjectManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'app_object'
        self.results = {
            'changed': False,
            'app_object': {},
        }
        self.resource = {}
        self.client: Apps = helper.get_client(module, Apps)

        super().__init__(module)

    @property
    def different(self):
        return False

    def existing(self):
        '''Return existing app object'''
        if self.resource != {}:
            return self.resource

        obj = self._app.get_object(self.module_params['id'])
        if obj.qType is not None:
            self.resource = obj
        return self.resource

    def create(self):
        obj = self._app.create_object(GenericObjectProperties(
            qInfo=NxInfo(qId=self.module_params['id'], qType=self.module_params['type'])
        ))
        self.resource = obj
        return obj

    def update(self):
        pass

    def delete(self):
        pass

    def execute(self):
        '''Execute the desired action according to map of states and actions.'''
        self._app = self.client.get(self.module_params['app_id'])
        with self._app.open():
            process_action = self.states_map[self.state]
            process_action()

        if self.module._diff:
            self.results['diff'] = self.diff

        return self.results


def main():
    module_args = dict(
        app_id=dict(type='str', required=True),
        id=dict(type='str', required=True),
        type=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    manager = QlikAppObjectManager(module)
    result = manager.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
