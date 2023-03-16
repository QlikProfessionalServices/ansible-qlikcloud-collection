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
  properties:
    description:
      - The properties of the object.
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
    properties:
      qProperty:
        qInfo:
          qId: EpsDdJ
          qType: my-custom-hypercube
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

import json

from qlik_sdk import Apps, GenericObjectProperties, GenericObjectEntry


class QlikAppObjectManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'app_object'
        self.results = {
            'changed': False,
            'app_object': {},
        }
        self.resource = {}
        self.desired = json.loads(module.params['properties'])
        self.client: Apps = helper.get_client(module, Apps)

        super().__init__(module)

    @property
    def different(self):
        return False

    def existing(self):
        '''Return existing app object'''
        if self.resource != {}:
            return self.resource

        try:
          obj = self._app.get_object(self.desired['qProperty']['qInfo']['qId'])
        except Exception as err:
            self.module.fail_json(
                msg='Error getting object: %s' % (to_native(err)),
                **self.results)
        if obj.qType is not None:
            self.resource = obj
            self.results.update({'app_object': obj})
        return self.resource

    def create(self):
        qInfo = GenericObjectProperties(qInfo=self.desired['qProperty']['qInfo'])

        try:
          obj = self._app.create_object(qInfo)
        except Exception as err:
            self.module.fail_json(
                msg='Error creating object: %s' % (to_native(err)),
                **self.results)

        try:
          obj.set_full_property_tree(GenericObjectEntry(**json.loads(self.module_params['properties'])))
        except Exception as err:
            self.module.fail_json(
                msg='Error setting full property tree: %s' % (to_native(err)),
                **self.results)

        self.resource = obj
        return obj

    def update(self):
        pass

    def delete(self):
        self._app.destroy_object(self.module_params['id'])

    def execute(self):
        '''Execute the desired action according to map of states and actions.'''
        try:
          self._app = self.client.get(self.module_params['app_id'])
        except Exception as err:
            self.module.fail_json(
                msg='Error getting app details: %s; %s' % (to_native(err), self.module_params['api_key']),
                **self.results)

        try:
            with self._app.open():
                process_action = self.states_map[self.state]
                process_action()
        except Exception as err:
            self.module.fail_json(
                msg='Error opening app: %s' % (to_native(err)),
                **self.results)

        if self.module._diff:
            self.results['diff'] = self.diff

        return self.results


def main():
    module_args = dict(
        app_id=dict(type='str', required=True),
        properties=dict(type='json', required=True),
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
