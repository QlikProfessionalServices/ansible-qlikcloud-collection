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
  id:
    description:
      - ID of the app
    required: false
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
      - reloaded
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
  # Create app in personal space
  qlik.cloud.app:
    name: Test
    description: My test app

  # Create app in shared space
  qlik.cloud.app:
    name: Test
    space: Development

  # Import a QVF
  qlik.cloud.app:
    file: Test.qvf
    name: Test App
    space: Development

  # Rename an app
  qlik.cloud.app:
    id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    name: My App

  # Change app owner
  qlik.cloud.app:
    name: Test
    owner_id: R2aCCzAa_fvf1s-NI9XU2y467l-g4sX6

  # Publish app to managed space
  qlik.cloud.app:
    origin_app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    space: Published Apps
    name: Sales Dashboard

  # Reload an app
  qlik.cloud.app:
    name: My App
    state: reloaded
'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError
import os


class QlikAppManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'app'
        self.results = {
            'changed': False,
            'app': {},
        }
        self.resource = {}
        self._space_id = ''
        self.desired = helper.construct_state_from_params(module.params, ignore_params=['file'])
        self.states_map = {
            'present': self.ensure_present,
            'absent': self.ensure_absent,
            'reloaded': self.reload}

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
        if self.resource:
            return self.resource.attributes

        if (app_id := self.module_params["id"]) == None:
            results = self.client.items.get_items(
                resourceType='app',
                name=self.module_params["name"],
                spaceId=self.space_id)
            if len(results) == 0:
                return {}

            for app in results:
                if app.name == self.module_params['name']:
                    app_id = app.resourceId
                    break

        self.resource = self.client.apps.get(app_id)
        if self.module_params["space"]:
            self.desired.update({'spaceId': self.space_id})

        return self.resource.attributes

    def update(self):
        if self.module.check_mode:
            self.results['app']=helper.asdict(self.resource)
            return self.resource.attributes

        changes_map = {
            'description': self.update_description,
            'ownerId': self.update_owner,
            'spaceId': self.update_space
        }

        for attr in self.changes:
            update_func = changes_map[attr]
            update_func(self.changes[attr])

        return helper.asdict(self.resource.attributes)

    def update_description(self, description: str):
        try:
            self.resource = self.resource.set(dict(description=description))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app description, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)

    def update_owner(self, id: str):
        try:
            self.resource = self.resource.set_owner(dict(ownerId=id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app owner, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results, app_id=self.resource.attributes.id)

    def update_space(self, name: str):
        try:
            self.resource = self.resource.set_space(dict(spaceId=self.space_id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating app space, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)

    def create(self):
        if self.module.check_mode:
            self.results['app']=helper.asdict(self.resource)
            return self.results

        self.desired['spaceId'] = self.space_id
        try:
            if self.module_params['file']:
                file_id = ''
                with open(self.module_params['file'], 'rb') as f:
                    params = {'filename': os.path.basename(self.module_params['file'])}
                    response = self.client.rest(
                        method='POST',
                        path='/temp-contents',
                        data=f,
                        params=params)
                    file_id = response.headers['Location'].split('/')[-1]
                self.resource = self.client.apps.import_app(
                    fileId=file_id,
                    spaceId=self.space_id)
                if self.module_params['description']:
                    self.update_description(self.module_params['description'])
            elif self.module_params['origin_app_id']:
                origin_app = self.client.apps.get(self.module_params['origin_app_id'])
                self.resource = origin_app.publish(dict(spaceId=self.space_id))
            else:
                self.resource = self.client.apps.create(dict(attributes=self.desired))

            if self.module_params['owner_id']:
                self.update_owner(self.module_params['owner_id'])
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating app, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)
        self.results['app']=helper.asdict(self.resource)
        return self.resource.attributes

    def reload(self):
        self.ensure_present()
        self.results['changed'] = True

        if self.module.check_mode:
            return

        try:
            self.client.reloads.create(dict(appId=self.resource.attributes.id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error reloading app, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)


def main():
    module_args = dict(
        id=dict(type='str', required=False),
        name=dict(type='str', required=True),
        space=dict(type='str', required=False),
        description=dict(type='str', required=False),
        owner_id=dict(type='str', required=False),
        origin_app_id=dict(type='str', required=False),
        file=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True),
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
