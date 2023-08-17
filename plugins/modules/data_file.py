#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: data_file
version_added: "0.1.0"
short_description: Manages data file in a Qlik Cloud space.
description:
    - Manages data file in a Qlik Cloud space.
options:
  name:
    description:
      - Name that will be given to the uploaded file. It should be noted that
        the '/' character in a data file name indicates a 'path' separator in a
        logical folder hierarchy for the name. Names that contain '/'s should
        be used with the assumption that a logical 'folder hierarchy' is being
        defined for the full pathname of that file. '/' is a significant
        character in the data file name, and may impact the behavior of future
        APIs which take this folder hierarchy into account.
    required: true
  app_id:
    description:
      - If this file should be bound to the lifecycle of a specific app, this
        is the ID of this app.
    required: false
  source_id:
    description:
      - If a SourceId is specified, this is the ID of the existing data file
        whose content should be copied into the specified data file. That is,
        instead of the file content being specified in the Data element, it is
        effectively copied from an existing, previously uploaded file.
    required: false
  space:
    description:
      - If present, this is the space that the upload should occur in the
        context of. If absent, the default is that the upload will occur in the
        context of the Personal space. If the DataFiles connection is different
        from the one specified when the file was last POSTed or PUT, this will
        result in a logical move of this file into the new space.
    required: false
  temp_content_file_id:
    description:
      - If a TempContentFileId is specified, this is the ID of a previously
        uploaded temporary content file whose content should be copied into the
        specified data file. That is, instead of the file content being
        specified in the Data element, it is effectively copied from an
        existing, previously uploaded file. The expectation is that this file
        was previously uploaded to the temporary content service, and the ID
        specified here is the one returned from the temp content upload request.
    required: false
  owner_id:
    description:
      - The user ID in uid format (string) of the data file owner
    required: false
  file:
    description:
      - Path to the file to be uploaded.
    required: true
  state:
    description:
      - State of the data file
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
  # Upload a new data file.
  qlik.cloud.data_file:
    name: MyFile.csv
    file: files/MyFile.csv

  # Change the owner of an existing data file.
  qlik.cloud.data_file:
    name: MyFile.csv
    owner_id: R2aCCzAa_fvf1s-NI9XU2y467l-g4sX6

  # Change the space that an existing data file resides in.
  qlik.cloud.data_file:
    name: MyFile.csv
    space: Development
'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

class QlikDataFileManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'data_file'
        self.results = {
            'changed': False,
            'data_file': {},
        }
        self.resource = {}
        self._space_id = ''
        self._conn_id = ''
        self.desired = helper.construct_state_from_params(module.params, ['file', 'space', 'owner_id'])

        super().__init__(module)

    @property
    def space_id(self):
        '''Return space ID from name'''
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

    @property
    def connection_id(self):
        '''Return connection ID for space'''
        if self._conn_id:
            return self._conn_id

        personal = False if self.space_id else True
        conn = self.client.datafiles.get_connections(
            spaceId=self.space_id,
            name='DataFiles',
            personal=personal)
        if len(conn) == 0:
            self.module.fail_json(msg="Connection not found!", **self.results)
        if len(conn) > 0:
            self._conn_id = conn[0].id

        return self._conn_id

    def existing(self):
        '''Return existing data file'''
        if self.resource != {}:
            return self.resource

        results = self.client.datafiles.get_data_files(
            connectionId=self.connection_id,
            name=self.module_params['name'])

        if len(results) > 0:
            self.resource = results[0]

        return self.resource

    def create(self):
        if self.module.check_mode:
            return self.existing()

        try:
            with open(self.module_params['file'], 'rb') as f:
                self.resource = self.client.datafiles.create(
                    **self.desired,
                    File=f,
                    connectionId=self.connection_id)
            if self.module_params['owner_id']:
                self.update_owner(self.module_params['owner_id'])
            return self.resource
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results)

    def update(self):
        if self.module.check_mode:
            self.results['data_file']=helper.asdict(self.app)
            return self.app.attributes

        changes_map = {
            'ownerId': self.update_owner,
            'space': self.update_space
        }

        for attr in self.changes:
            update_func = changes_map[attr]
            update_func(self.changes[attr])

        return helper.asdict(self.resource)

    def update_owner(self, id: str):
        try:
            self.app = self.resource.change_owner(dict(ownerId=id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating data-file owner, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results, app_id=self.app.attributes.id)

    def update_space(self, name: str):
        try:
            self.app = self.resource.change_space(dict(spaceId=self.space_id))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating data-file space, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        app_id=dict(type='str', required=False),
        source_id=dict(type='str', required=False),
        space=dict(type='str', required=False),
        temp_content_file_id=dict(type='str', required=False),
        owner_id=dict(type='str', required=False),
        file=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikDataFileManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
