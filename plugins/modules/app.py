#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: app
version_added: "0.1.0"
short_description: Manages apps in Qlik Cloud.
description:
    - Manages apps in Qlik Cloud.
options:
  name:
    description:
      - Name of the app
    required: true
  space:
    description:
      - Name of space
    required: false
  description:
    description: The description of the space
    required: false
  owner_id:
    description: The user ID in uid format (string) of the space owner
    required: false
  origin_app_id:
    description: The ID of the origin app used to publish the app
    required: false
  file:
    description: Path to a QVF file to import
    required: false
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
  # Create app
  app:
    name: Test
'''


from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils import helper
from ansible.module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError


class QlikAppManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'app'
        self.results = {
            'changed': False,
            'app': {},
        }
        self.app = {}
        self._space_id = ''
        self.desired = helper.construct_state_from_params(module.params, ignore_params=['file'])

        super().__init__(module)

    @property
    def space_id(self):
        if self._space_id:
            return self._space_id
        if self.module_params['space'] == '':
            return ''

        space_results = self.client.spaces.get_spaces(name=self.module_params['space'])
        if len(space_results) == 0:
            self.module.fail_json(msg="Space not found!", **self.results)
        for space in space_results:
            if space.name == self.module_params['space']:
                self._space_id = space.id
                return self._space_id

    def existing(self):
        '''Return existing app'''
        if self.app:
            return self.app.attributes

        results = self.client.items.get_items(
            resourceType='app',
            name=self.module_params["name"],
            spaceId=self.space_id)
        if len(results) == 0:
            return {}

        for app in results:
            if app.name == self.module_params['name']:
                self.app = self.client.apps.get(app.resourceId)
                return self.app.attributes

        return self.app

    def update(self):
        if self.module.check_mode:
            self.results['app']=helper.asdict(self.app)
            return self.app.attributes

        changes_map = {
            'description': self.update_description,
            'ownerId': self.update_owner,
            'space': self.update_space
        }

        for attr in self.changes:
            update_func = changes_map[attr]
            update_func(self.changes[attr])

        return helper.asdict(self.app.attributes)

    def update_description(self, description: str):
        try:
            self.app = self.app.set(dict(description=description))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app description, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)

    def update_owner(self, id: str):
        try:
            self.app = self.app.set_owner(dict(ownerId=id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app owner, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results, app_id=self.app.attributes.id)

    def update_space(self, name: str):
        try:
            self.app = self.app.set_space(dict(spaceId=self.space_id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app space, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)

    def create(self):
        if self.module.check_mode:
            self.results['app']=helper.asdict(self.app)
            return self.results

        self.desired['spaceId'] = self.space_id
        try:
            if self.module_params['file']:
                self.app = self.client.apps.import_app(dict(
                    data=self.desired['file'],
                    name=self.desired['name'],
                    spaceId=self.space_id,
                ))
                if self.module_params['description']:
                    self.update_description(self.module_params['description'])
            elif self.module_params['origin_app_id']:
                origin_app = self.client.apps.get(self.module_params['origin_app_id'])
                self.app = origin_app.publish(dict(spaceId=self.space_id))
            else:
                self.app = self.client.apps.create(dict(attributes=self.desired))

            if self.module_params['owner_id']:
                self.update_owner(self.module_params['owner_id'])
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating app, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)
        self.results['app']=helper.asdict(self.app)
        return self.app.attributes


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        space=dict(type='str', required=False),
        description=dict(type='str', required=False),
        owner_id=dict(type='str', required=False),
        origin_app_id=dict(type='str', required=False),
        file=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    apps = QlikAppManager(module)
    result = apps.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
